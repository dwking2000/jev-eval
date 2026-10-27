#!/bin/bash
# Orchestrates: remaining data builds -> jev evals (0.8b+2b) -> pplx eval. Logs to synth/run_all.log (markers: "== ")
cd /c/Users/Doug/jev-eval; export PYTHONUTF8=1 SYNTH_CWD="C:/Users/Doug/jev-eval/synth/work"
PY=venv/Scripts/python.exe; OL=http://localhost:11434
mkdir -p results

echo "== waiting for gemma v3 pipeline and claude v4c"
until grep -q "ALL DONE" synth/run_v3.log; do sleep 30; done
until grep -q "prompt_router: generated" synth/v4c/gen.log 2>/dev/null; do sleep 20; done

echo "== gen v4g (gemma3:27b, tuned prompts)"; $PY -I tools/synth/harness4.py gen --model gemma3:27b --n 100 --out synth/v4g --seed 41
echo "== panel v4c";  $PY -I tools/synth/harness4.py panel --out synth/v4c
echo "== build v4c";  $PY -I tools/synth/harness4.py build --out synth/v4c --source claude-v4
echo "== panel v4g";  $PY -I tools/synth/harness4.py panel --out synth/v4g
echo "== build v4g";  $PY -I tools/synth/harness4.py build --out synth/v4g --source gemma-v4

echo "== unloading ollama models"
for m in gemma3:27b gpt-oss:20b olmo2:13b phi4:latest; do curl -s $OL/api/generate -d "{\"model\":\"$m\",\"keep_alive\":0}" >/dev/null; done
sleep 20

# name|file  (labels: v1 = claude verifier; others = non-claude non-qwen panel majority)
DS="v1_claude_clean|synth/v1/eval.jsonl
v2_claude_dirty|synth/v2/p_eval.jsonl
v3_gemma_dirty|synth/v3/p_eval.jsonl
v4c_claude_tuned|synth/v4c/p_eval.jsonl
v4g_gemma_tuned|synth/v4g/p_eval.jsonl
v2_amb|synth/v2/p_amb_eval.jsonl
v3_amb|synth/v3/p_amb_eval.jsonl
v4c_amb|synth/v4c/p_amb_eval.jsonl
v4g_amb|synth/v4g/p_amb_eval.jsonl"

wait_health() { for i in $(seq 1 80); do curl -s -m 3 $1 | grep -q -E '"status":"(ok|ready)"' && return 0; sleep 10; done; return 1; }

echo "== start jev servers"
nohup venv/Scripts/jev-style.exe serve --release 2b   --backend torch --device cuda --port 8765 > synth/jev2b.log 2>&1 &
nohup venv/Scripts/jev-style.exe serve --release 0.8b --backend torch --device cuda --port 8766 > synth/jev08.log 2>&1 &
wait_health http://127.0.0.1:8765/healthz && wait_health http://127.0.0.1:8766/healthz || echo "JEV SERVERS FAILED"
echo "$DS" | while IFS='|' read name file; do
  [ -s "$file" ] || { echo "skip $name (no file)"; continue; }
  echo "-- jev eval $name"; venv/Scripts/jev-style.exe eval "$file" --server 2b=http://127.0.0.1:8765 --server 08b=http://127.0.0.1:8766 --json results/${name}_jev.json > results/${name}_jev.txt 2>&1
done
echo "== stop jev servers"; taskkill //F //IM jev-style.exe >/dev/null 2>&1; sleep 10

echo "== start pplx (nf4)"
nohup pplx-venv/Scripts/python.exe tools/pplx_serve_nf4.py > synth/pplx.log 2>&1 &
wait_health http://127.0.0.1:8767/health || echo "PPLX FAILED"
echo "$DS" | while IFS='|' read name file; do
  [ -s "$file" ] || continue
  echo "-- pplx eval $name"; venv/Scripts/jev-style.exe eval "$file" --server pplx=http://127.0.0.1:8767 --model pplx=autojev --json results/${name}_pplx.json > results/${name}_pplx.txt 2>&1
done
echo "== EVALS DONE"
