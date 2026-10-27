"""v4 prompt/sampling profile (tuned after reading v2 samples). Overrides only generation; labelling/build come from harness3.

  python harness4.py gen   --model sonnet|gemma3:27b --n 100 --out DIR
  python harness4.py panel --out DIR
  python harness4.py build --out DIR --source NAME
"""
import argparse, collections, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H, harness2 as H2, harness3 as H3
from harness import FAMILIES, spec_text

STYLES4 = [("mundane", .30), ("lure", .20), ("messy_context", .12), ("sparse", .10), ("ambiguous", .20), ("injection", .08)]
STYLE_HELP4 = {
    "mundane": "An ordinary, boring, everyday input. No drama, no distinctive incident. The answers follow plainly from what is written.",
    "lure": "HARD NEGATIVE: surface cues (keywords, tone, format) point toward a WRONG option, yet the targets are the best answers on a careful read.",
    "messy_context": "The signal is a small part of the text; the rest is realistic clutter that belongs in this kind of input (history, boilerplate, side comments).",
    "sparse": "Very short and under-specified (3-15 words). Real senders often omit context. The targets must still be the best reading.",
    "ambiguous": "GENUINELY AMBIGUOUS on the questions in 'ambiguous_on': two options are defensible to a thoughtful reader. The target is slightly better supported, the alternate a real contender; not contrived. Give the alternate in 'alt'.",
    "injection": "Includes an embedded instruction or claimed label that a naive classifier might obey, DISGUISED as content that could plausibly appear there (a forwarded note, a pasted policy line, an auto-reply, a signature tagline). NEVER use phrases like 'ignore previous instructions' or 'note to AI'. It must not change the true answers.",
}
UNIVERSAL = ["typos and autocorrect substitutions", "all-lowercase, little punctuation", "truncated mid-sentence", "emoji or chat slang",
             "inconsistent spacing / stray line breaks", "very terse", "rambles, buries the point late", "mixed languages or a non-native phrasing",
             "refers to 'this'/'it' without saying what (missing context)", "two unrelated topics in one message"]
BY_FAMILY = {
    "support_triage": ["quoted earlier message below", "pasted order confirmation snippet", "signature block", "ALL CAPS in a few words"],
    "email_triage": ["quoted reply chain (> lines)", "signature block", "legal/confidentiality footer", "auto-generated footer or unsubscribe line", "forwarded with a one-line comment"],
    "tool_call_guard": ["agent's chatty note or comment attached to the call", "extra irrelevant arguments", "a long command with pipes and flags", "relative paths and shell variables"],
    "incident_log": ["interleaved unrelated log lines", "log lines in mixed formats", "truncated stack trace", "noisy repeated warnings"],
    "prompt_router": ["pasted snippet of code or text with the ask below it", "a pasted error message", "ALL CAPS in a few words"],
}
INDUSTRIES = ("veterinary clinic;bike shop;regional bank;SaaS billing tool;city water utility;university registrar;online grocery;dental office;freight broker;"
              "indie game studio;property management;hospital scheduling;airline loyalty program;law firm;solar installer;car rental;podcast hosting;"
              "language-learning app;hardware store;nonprofit donations;telecom provider;co-working space;insurance claims;ticketing platform;"
              "pharmacy;cloud hosting provider;high-school IT desk;food delivery;fitness studio;e-commerce furniture;payroll provider;"
              "smart-home devices;public library;construction firm;travel agency;crypto exchange;3D-printing marketplace;HR software;church office;farm co-op").split(";")
PERSONAS = H2.PERSONAS + ["someone who does this all day and writes shorthand", "first message ever sent to this address", "automated system or script"]

MACHINE_PERSONAS = {
    "incident_log": ["on-call engineer pasting an alert with a quick comment", "automated alerting system, templated text only", "terse SRE", "monitoring bot with a verbose template"],
    "tool_call_guard": ["AI coding agent that adds terse notes", "AI coding agent that adds verbose, chatty notes", "automated agent with no notes", "developer-written script making the call"],
}

def sample_targets4(fam, n, rng):
    rng = random.Random(f"{rng.random()}-{fam}")      # independent stream per family: settings/personas don't repeat across families
    personas = MACHINE_PERSONAS.get(fam, PERSONAS)
    used = collections.Counter(); out = []
    styles = [s for s, _ in STYLES4]; w = [x for _, x in STYLES4]; pool = UNIVERSAL + BY_FAMILY[fam]
    for i in range(n):
        t = {}
        for qid, qq in FAMILIES[fam]["questions"].items():
            p = H2.SKEW[fam][qid]
            if qq["type"] == "noul": t[qid] = "true" if rng.random() < p else "false"
            elif qq["type"] == "choice": t[qid] = rng.choices(list(qq["criteria"]), p)[0]
            else: t[qid] = str(rng.choices(range(len(qq["criteria"])), p)[0])
        st = rng.choices(styles, w)[0]
        k = 0 if st in ("mundane", "sparse") and rng.random() < .6 else rng.choice([0, 1, 1, 1, 2])
        cor = []
        for _ in range(k):                                   # rarer-so-far corruptions are likelier
            c = rng.choices(pool, [1 / (1 + used[x]) ** 2 for x in pool])[0]
            if c not in cor: cor.append(c); used[c] += 1
        item = {"id": f"{fam}-e{i:04d}", "style": st, "targets": t, "persona": rng.choice(personas), "corruptions": cor,
                "setting": rng.choice(INDUSTRIES)}
        if st == "ambiguous": item["ambiguous_on"] = rng.sample(list(t), rng.choice([1, 1, 2]))
        out.append(item)
    return out

def gen_batch4(fam, batch):
    spec = FAMILIES[fam]
    items = [{**{k: b[k] for k in ("id", "targets", "persona", "corruptions", "setting")}, "style": b["style"],
              "style_rule": STYLE_HELP4[b["style"]], **({"ambiguous_on": b["ambiguous_on"]} if "ambiguous_on" in b else {})} for b in batch]
    prompt = f"""You are building a realistic test set for a text classifier. Most real inputs are mundane, partial and slightly sloppy; they are rarely dramatic, and they do not read like examples.
Input kind: {spec["state"]}
Questions the classifier will answer (score levels are numbered from 0):
{spec_text(fam)}

For each item write ONE input whose best answers are the given targets, following its style_rule.
- Setting: the input arises in the item's "setting" (an organisation/industry). Use it naturally; do not name a real company.
- Write as the item's persona would. Apply ONLY the listed corruptions, concretely and lightly, as a real writer would produce them. If the list is empty the text is clean. Do NOT add signatures, footers, HTML, quoted history, placeholders or typos unless a listed corruption calls for it.
- Every item in the batch must differ in scenario, length (from a few words to several paragraphs), structure and vocabulary. Do not reuse a phrase, a name, or a device across items. Avoid cliches ('Dear Sir', 'I hope this finds you well', 'Sarah', 'Acme'), and avoid the self-correction pattern ('actually, never mind').
- People do not explain their situation neatly. Leave out context a real sender would leave out. Do not make the signal tidy and the noise separate.
- The text must be ONLY the raw input as a real system would deliver it: no narrator commentary, nothing that states how risky/urgent/severe it is or which category it belongs to.
- For style "ambiguous": add "alt": {{"<question id>": "<the defensible alternate answer, same format as targets>"}} for each question in ambiguous_on.
- If a target combination is truly contradictory, set "impossible": true and leave state empty.
Return a JSON list: [{{"id": "...", "state": "<the input>", "alt": {{}}, "impossible": false}}, ...]

Items:
{json.dumps(items, indent=1)}"""
    res = H2.claude(prompt, H.GEN_MODEL) or []
    by = {r.get("id"): r for r in res if isinstance(r, dict)}
    out = []
    for b in batch:
        r = by.get(b["id"])
        if r and not r.get("impossible") and r.get("state"):
            st = r["state"] if isinstance(r["state"], str) else json.dumps(r["state"], ensure_ascii=False)
            out.append({**b, "state": st, "alt": {k: str(v).lower() for k, v in (r.get("alt") or {}).items()}})
    return out

H2.sample_targets2, H2.gen_batch2 = sample_targets4, gen_batch4

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--out", required=True); ap.add_argument("--model", default="sonnet")
    ap.add_argument("--n", type=int, default=100); ap.add_argument("--seed", type=int, default=31); ap.add_argument("--source", default="unknown")
    ap.add_argument("--models", default=",".join(H3.PANEL)); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    if a.cmd == "gen":
        if a.model in ("sonnet", "opus", "haiku"):          # Claude generator via claude -p
            H.GEN_MODEL = a.model
            for fam in FAMILIES:
                rows = [r for part in H.pmap(lambda b: gen_batch4(fam, b), H.chunks(sample_targets4(fam, a.n, random.Random(a.seed)), 8), 4) for r in part]
                with open(os.path.join(a.out, f"gen_{fam}.jsonl"), "a", encoding="utf-8") as f:
                    for r in rows: f.write(json.dumps({**r, "generator": a.model}, ensure_ascii=False) + "\n")
                print(f"{fam}: generated {len(rows)}/{a.n}  cost so far ${H._cost[0]:.2f}", flush=True)
        else:
            H3.cmd_gen(a.model, a.n, a.out, a.seed)
    elif a.cmd == "panel": H3.cmd_panel(a.out, a.models.split(","))
    elif a.cmd == "build": H3.cmd_build(a.out, a.source, a.models.split(","))
