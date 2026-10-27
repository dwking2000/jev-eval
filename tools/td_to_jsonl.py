"""Convert LocalLLaMA/typed-decisions test parquet -> jev-style eval JSONL (label = gold argmax)."""
import json, sys
import pyarrow.parquet as pq

src, dst = sys.argv[1], sys.argv[2]
n = 0
with open(dst, "w", encoding="utf-8") as f:
    for r in pq.read_table(src).to_pylist():
        qs, gold = json.loads(r["questions"]), json.loads(r["gold"])
        for qid, q in qs.items():
            q["label"] = gold[qid]["label"]
        f.write(json.dumps({"state": json.loads(r["state"]), "questions": qs}, ensure_ascii=False) + "\n")
        n += 1
print(n, "rows ->", dst)
