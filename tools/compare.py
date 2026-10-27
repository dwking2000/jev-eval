import json, math, random, collections
j = json.load(open('results_td_jev.json'))['results']
p = json.load(open('results_td_pplx.json'))['results']
E = {'jev-2b': j['2b'], 'jev-0.8b': j['08b'], 'pplx-27b-nf4': p['pplx']}
key = lambda x: (x['row'], x['qid'])
idx = {n: {key(x): x for x in rows} for n, rows in E.items()}
common = sorted(set.intersection(*[set(d) for d in idx.values()]))
def hit(x): return max(x['probs'], key=x['probs'].get) == x['label']
def brier(x): return sum((p - (k == x['label'])) ** 2 for k, p in x['probs'].items())
print('common questions', len(common))
for n, d in idx.items():
    a = [hit(d[k]) for k in common]; b = [brier(d[k]) for k in common]
    print(f"{n:14s} acc {sum(a)/len(a):.3f}  brier {sum(b)/len(b):.3f}")
    bt = collections.defaultdict(list)
    for k in common: bt[d[k]['type']].append(hit(d[k]))
    print('   by type', {t: round(sum(v)/len(v), 3) for t, v in bt.items()})
rows = sorted({k[0] for k in common}); random.seed(0)
def boot(a, b):
    diffs = []
    for _ in range(2000):
        s = [random.choice(rows) for _ in rows]; num = n = 0
        for r in s:
            for k in by_row[r]: num += hit(idx[a][k]) - hit(idx[b][k]); n += 1
        diffs.append(num / n)
    diffs.sort(); return diffs[50], diffs[1950]
by_row = collections.defaultdict(list)
for k in common: by_row[k[0]].append(k)
for a, b in [('pplx-27b-nf4', 'jev-0.8b'), ('pplx-27b-nf4', 'jev-2b')]:
    d = sum(hit(idx[a][k]) - hit(idx[b][k]) for k in common) / len(common)
    lo, hi = boot(a, b); print(f"{a} - {b}: acc {d*100:+.1f} pts  95% CI [{lo*100:+.1f}, {hi*100:+.1f}]")
