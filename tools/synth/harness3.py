"""v3: local (Ollama) generator + a non-Claude, non-Qwen labeler panel, reusing the v2 'dirty' prompts.

  python harness3.py gen   --model gemma3:27b --n 80 --out DIR      # generate rows locally (temp 1.0, min_p 0.05)
  python harness3.py panel --out DIR [--models a,b,c]               # blind-label DIR/gen_*.jsonl with each panelist
  python harness3.py build --out DIR --source gemma3-27b            # keep a label only if >=2 of 3 panelists agree with the plan
Works on any dir holding gen_<family>.jsonl (incl. the Claude-written v2 dir, to relabel it with the panel).
"""
import argparse, json, os, statistics, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H, harness2 as H2
from harness import FAMILIES, pmap, chunks

HOST = os.environ.get("OLLAMA_URL", "http://localhost:11434")
PANEL = ["gpt-oss:20b", "olmo2:13b", "phi4:latest"]

def route(prompt, model, system="You output only valid JSON, no prose, no code fences."):
    """Drop-in for harness.claude: model 'ollama:<name>' goes to Ollama, anything else to claude -p."""
    if not model.startswith("ollama:"): return H.claude(prompt, model, system)
    name, gen = model[7:], model.endswith("@gen")
    if gen: name = name[:-4]
    opts = {"temperature": 1.0, "top_p": 0.95, "min_p": 0.05, "repeat_penalty": 1.05} if gen else {"temperature": 0}
    opts.update(num_ctx=16384, num_predict=8192)
    body = json.dumps({"model": name, "stream": False, "options": opts,
                       "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]}).encode()
    for attempt in range(3):
        try:
            req = urllib.request.Request(HOST + "/api/chat", body, {"content-type": "application/json"})
            txt = json.load(urllib.request.urlopen(req, timeout=900))["message"]["content"]
            a, b = txt.find("["), txt.rfind("]")
            return json.loads(txt[a:b + 1])
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
    print("local call failed:", name, err, file=sys.stderr); return None

H2.claude = route          # harness2's batch functions now resolve their model through the router

def tag(m): return m.split(":")[0].replace("/", "-")

def cmd_gen(model, n, out, seed):
    H.GEN_MODEL = f"ollama:{model}@gen"
    for fam in FAMILIES:
        rows = [r for part in pmap(lambda b: H2.gen_batch2(fam, b), chunks(H2.sample_targets2(fam, n, __import__("random").Random(seed)), 8), 2) for r in part]
        with open(os.path.join(out, f"gen_{fam}.jsonl"), "a", encoding="utf-8") as f:
            for r in rows: f.write(json.dumps({**r, "generator": model}, ensure_ascii=False) + "\n")
        print(f"{fam}: generated {len(rows)}/{n}", flush=True)

def cmd_panel(out, models):
    for m in models:                                   # one model at a time: Ollama keeps a single model loaded
        H.VERIFY_MODEL = f"ollama:{m}"
        for fam in FAMILIES:
            p = os.path.join(out, f"gen_{fam}.jsonl")
            if not os.path.exists(p): continue
            rows = [json.loads(l) for l in open(p, encoding="utf-8")]
            got = {}
            for d in pmap(lambda b: H2.verify_batch2(fam, b), chunks(rows, 10), 2): got.update(d)
            json.dump(got, open(os.path.join(out, f"pan_{fam}.{tag(m)}.json"), "w"))
            print(f"{m:14s} {fam}: labelled {len(got)}/{len(rows)}", flush=True)

def cmd_build(out, source, models):
    ev, meta, amb_ev, amb_meta, rej = [], [], [], [], []
    stat = {m: [0, 0] for m in models}
    for fam in FAMILIES:
        p = os.path.join(out, f"gen_{fam}.jsonl")
        vers = [json.load(open(os.path.join(out, f"pan_{fam}.{tag(m)}.json"))) if os.path.exists(os.path.join(out, f"pan_{fam}.{tag(m)}.json")) else {} for m in models]
        if not os.path.exists(p): continue
        for r in map(json.loads, open(p, encoding="utf-8")):
            vs = [v.get(r["id"]) for v in vers]
            if sum(x is not None for x in vs) < 2: continue
            real = statistics.median([x["_realism"] for x in vs if x])
            if real <= 2: rej.append({**r, "realism": real}); continue
            qs, kept = {}, 0
            for qid, qq in FAMILIES[fam]["questions"].items():
                d = {"type": qq["type"], "instructions": qq["instructions"]}
                if qq["criteria"] is not None: d["criteria"] = qq["criteria"]
                lab = r["targets"][qid]
                votes = [x.get(qid) == lab for x in vs if x]
                for m, x in zip(models, vs):
                    if x: stat[m][1] += 1; stat[m][0] += x.get(qid) == lab
                if r["style"] == "ambiguous":
                    if qid not in r.get("alt", {}): continue
                    ok = True
                else: ok = sum(votes) * 2 > len(votes)            # strict majority of the panel agrees with the plan
                if ok: d["label"] = lab if qq["type"] != "noul" else lab == "true"; kept += 1
                qs[qid] = d
            if not kept: continue
            m_ = {"id": r["id"], "family": fam, "style": r["style"], "source": source, "realism": real, "persona": r["persona"],
                  "corruptions": r["corruptions"], "alt": r.get("alt", {})}
            (amb_ev if r["style"] == "ambiguous" else ev).append({"state": r["state"], "questions": qs})
            (amb_meta if r["style"] == "ambiguous" else meta).append(m_)
    for name, rows in (("p_eval.jsonl", ev), ("p_meta.jsonl", meta), ("p_amb_eval.jsonl", amb_ev), ("p_amb_meta.jsonl", amb_meta), ("p_rejected.jsonl", rej)):
        with open(os.path.join(out, name), "w", encoding="utf-8") as f:
            for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[{source}] eval rows {len(ev)}, ambiguous rows {len(amb_ev)}, rejected {len(rej)}")
    for m, (a, t) in stat.items(): print(f"  panelist {m:14s} agrees with plan on {a}/{t} = {a/max(t,1):.0%}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--out", required=True); ap.add_argument("--model", default="gemma3:27b")
    ap.add_argument("--n", type=int, default=80); ap.add_argument("--seed", type=int, default=21); ap.add_argument("--source", default="unknown")
    ap.add_argument("--models", default=",".join(PANEL)); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    if a.cmd == "gen": cmd_gen(a.model, a.n, a.out, a.seed)
    elif a.cmd == "panel": cmd_panel(a.out, a.models.split(","))
    elif a.cmd == "build": cmd_build(a.out, a.source, a.models.split(","))
