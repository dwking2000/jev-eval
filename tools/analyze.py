"""Summarise results/*.json: per-dataset accuracy/Brier per engine, paired bootstrap, generator-source bias, ambiguous-set calibration.
Run: python -I tools/analyze.py   (reads results/, synth/*/p_amb_meta.jsonl; writes results/summary.md)"""
import json, os, random, collections

R = "results"
CLEAN = ["v1_claude_clean", "v2_claude_dirty", "v3_gemma_dirty", "v4c_claude_tuned", "v4g_gemma_tuned"]
AMB = {"v2_amb": "synth/v2", "v3_amb": "synth/v3", "v4c_amb": "synth/v4c", "v4g_amb": "synth/v4g"}
NAMES = {"2b": "jev-2b", "08b": "jev-0.8b", "pplx": "pplx-27b-nf4"}

def load(ds):
    E = {}
    for suffix in ("jev", "pplx"):
        p = f"{R}/{ds}_{suffix}.json"
        if os.path.exists(p):
            for e, rows in json.load(open(p))["results"].items(): E[NAMES.get(e, e)] = {(x["row"], x["qid"]): x for x in rows}
    return E

top = lambda x: max(x["probs"], key=x["probs"].get)
hit = lambda x: top(x) == x["label"]
brier = lambda x: sum((p - (k == x["label"])) ** 2 for k, p in x["probs"].items())

def boot(E, a, b, keys, f, n=1500, seed=0):
    by = collections.defaultdict(list)
    for k in keys: by[k[0]].append(k)
    rows = sorted(by); rng = random.Random(seed); d = []
    for _ in range(n):
        s = [rng.choice(rows) for _ in rows]; tot = c = 0
        for r in s:
            for k in by[r]: tot += f(E[a][k]) - f(E[b][k]); c += 1
        d.append(tot / c)
    d.sort(); return d[int(.025 * n)], d[int(.975 * n)]

out = ["# Synthetic eval summary\n"]; acc_tab = {}
for ds in CLEAN:
    E = load(ds)
    if len(E) < 2: out.append(f"## {ds}: missing engines {list(E)}\n"); continue
    keys = sorted(set.intersection(*[set(v) for v in E.values()]))
    out.append(f"## {ds}  ({len(keys)} questions, {len({k[0] for k in keys})} rows)\n\n| engine | accuracy | Brier | mean top-p |\n|---|---|---|---|")
    for e, d in sorted(E.items()):
        a = sum(hit(d[k]) for k in keys) / len(keys); b = sum(brier(d[k]) for k in keys) / len(keys); c = sum(max(d[k]["probs"].values()) for k in keys) / len(keys)
        acc_tab[(ds, e)] = a; out.append(f"| {e} | {a:.1%} | {b:.3f} | {c:.2f} |")
    if "pplx-27b-nf4" in E:
        for other in ("jev-0.8b", "jev-2b"):
            if other in E:
                d = sum(hit(E["pplx-27b-nf4"][k]) - hit(E[other][k]) for k in keys) / len(keys); lo, hi = boot(E, "pplx-27b-nf4", other, keys, hit)
                out.append(f"\npplx − {other}: {d*100:+.1f} pts  (95% CI {lo*100:+.1f} to {hi*100:+.1f})")
    out.append("")

out.append("## Generator-source effect (accuracy, same prompt generation; Claude-written vs Gemma-written)\n\n| engine | v2 Claude | v3 Gemma | gap | v4 Claude | v4 Gemma | gap |\n|---|---|---|---|---|---|---|")
for e in NAMES.values():
    g = lambda ds: acc_tab.get((ds, e))
    v = [g("v2_claude_dirty"), g("v3_gemma_dirty"), g("v4c_claude_tuned"), g("v4g_gemma_tuned")]
    if None in v: continue
    out.append(f"| {e} | {v[0]:.1%} | {v[1]:.1%} | {(v[0]-v[1])*100:+.1f} | {v[2]:.1%} | {v[3]:.1%} | {(v[2]-v[3])*100:+.1f} |")
out.append("\nIf the Qwen-derived engines gain MORE from Claude-written text than a non-Qwen reference would, the gap column is evidence of source bias. We only have Qwen-derived engines here, so compare gap sizes between engines.\n")

out.append("## Ambiguous items (two defensible answers). Good model: still right under either label, but LESS confident.\n\n| set | engine | n | acc (primary) | acc (either) | mean top-p | clean-set mean top-p |\n|---|---|---|---|---|---|---|")
for ds, d in AMB.items():
    E = load(ds); mp = f"{d}/p_amb_meta.jsonl"
    if not E or not os.path.exists(mp): continue
    meta = [json.loads(l) for l in open(mp, encoding="utf-8")]
    clean_ds = {"v2_amb": "v2_claude_dirty", "v3_amb": "v3_gemma_dirty", "v4c_amb": "v4c_claude_tuned", "v4g_amb": "v4g_gemma_tuned"}[ds]
    C = load(clean_ds)
    for e, dd in sorted(E.items()):
        either = lambda x: top(x) in (x["label"], str(meta[x["row"]]["alt"].get(x["qid"]))) if x["row"] < len(meta) else hit(x)
        n = len(dd); pa = sum(hit(x) for x in dd.values()) / n; ea = sum(either(x) for x in dd.values()) / n; mt = sum(max(x["probs"].values()) for x in dd.values()) / n
        cm = (sum(max(x["probs"].values()) for x in C[e].values()) / len(C[e])) if e in C and C[e] else float("nan")
        out.append(f"| {ds} | {e} | {n} | {pa:.1%} | {ea:.1%} | {mt:.2f} | {cm:.2f} |")

open(f"{R}/summary.md", "w", encoding="utf-8").write("\n".join(out)); print("\n".join(out))
