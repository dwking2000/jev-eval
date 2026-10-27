#!/bin/bash
cd /c/Users/Doug/jev-eval; export PYTHONUTF8=1
PY=venv/Scripts/python.exe; H=tools/synth/harness3.py
echo "== gen v3 (gemma3:27b)"; $PY -I $H gen --model gemma3:27b --n 80 --out synth/v3
echo "== panel v3";            $PY -I $H panel --out synth/v3
echo "== build v3";            $PY -I $H build --out synth/v3 --source gemma3-27b
echo "== waiting for claude v2"; until [ -f synth/v2/eval.jsonl ]; do sleep 30; done
echo "== panel v2";            $PY -I $H panel --out synth/v2
echo "== build v2 (panel labels)"; $PY -I $H build --out synth/v2 --source claude-sonnet
echo "== ALL DONE"
