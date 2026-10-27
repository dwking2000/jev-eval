# jev-eval

Evaluating small calibrated "decision" classifiers ([jev-style](https://github.com/lawrence3699/jev-style) 0.8B / 2B and `perplexity-ai/pplx-decider-v1.1-27b`, run 4-bit NF4 on a 24 GB GPU) on synthetic task data.

- `tools/` - launchers and analysis (`pplx_serve_nf4.py`, `analyze.py`, `compare.py`)
- `tools/synth/` - synthetic-data harness: labels are planned first, text is generated (Claude or Gemma 3 27B), then a non-Claude, non-Qwen panel (gpt-oss 20B, OLMo 2 13B, Phi-4) blind-labels it; strict majority wins
- `synth/` - generated datasets (v1 to v4)
- `results/` - per-dataset eval output; `results/summary.md` has the tables

Headline: pplx-27b (NF4) beat jev-2b and jev-0.8b on all five synthetic sets (+4 to +22 accuracy points). All data is synthetic; labels are model-derived, so treat it as a rough guide, not a benchmark. Some `synth` rows are deliberately adversarial (prompt injection, risky commands).
