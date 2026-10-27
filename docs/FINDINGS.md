# Findings and recommendations

## What this is
jev-style is a calibrated decision classifier (Qwen3.5 0.8B / 2B fine-tune), not a chat model. It answers typed questions (yes/no, choice, score) about a text in one forward pass via `POST /v1/systemone`. Stock llama.cpp, Ollama, LM Studio and LiteLLM cannot serve it.

## Results (synthetic data, accuracy)
Five synthetic sets, labels planned first and checked by a non-Claude, non-Qwen panel (gpt-oss 20B, Phi-4, OLMo 2 13B). pplx-decider-27b ran 4-bit (NF4). Full tables: `results/summary.md`.

| Dataset | jev 0.8B | jev 2B | pplx 27B (4-bit) |
|---|---|---|---|
| v1 Claude, clean | 70.8% | 76.0% | 93.0% |
| v2 Claude, dirty | 79.8% | 82.8% | 92.4% |
| v3 Gemma, dirty | 72.4% | 79.7% | 83.8% |
| v4 Claude, tuned | 77.2% | 81.3% | 91.3% |
| v4 Gemma, tuned | 79.1% | 80.0% | 86.9% |

- pplx won every set (+4 to +22 points) and has the best Brier scores. Cost: ~640 ms and ~15 GB VRAM per instance vs ~100 ms for jev.
- On the public typed-decisions benchmark the ranking flipped (jev 0.8B 79.1%, pplx 73.9%, jev 2B 63.0%): it scores agreement with a small teacher model, not ground truth. Which benchmark resembles your tasks decides the winner; test on 20 to 50 real labelled examples.
- Generator bias: pplx scores higher on Claude-written than Gemma-written text, weak and confounded evidence (all three engines are Qwen-derived).
- Ambiguous items: all models are right under either defensible label 77 to 99% of the time and lower their confidence by only ~0.08.
- Caveats: labels are model-derived; OLMo was a weak labeler (46 to 56% agreement); the 27B ran quantised; everything is synthetic.

## Recommendation
- **Production (internal, mostly idle):** jev 0.8B or 2B on your existing EKS cluster, CPU first. See `deploy/README.md`. Use pplx-27b only if its accuracy gain justifies a 24 GB GPU.
- **Pattern:** act when confidence clears a threshold derived from your own labelled eval; otherwise fall back to an LLM via LiteLLM. Run in shadow mode first.
- **Docker** adds negligible overhead on Linux (CPU or GPU with the NVIDIA toolkit).

## Local use on a Mac (M4+)
- Run natively, not in Docker: Docker Desktop's Linux VM cannot use the GPU, which rules out MLX/Metal.
- `uv venv && uv pip install "jev-style[mlx]"` then `jev-style serve` (auto-selects MLX; `--precision 8bit` for 0.8 GB, `--release 2b` for the 2B). README reports ~0.15 to 0.2 s per short request on an M1 Max; not measured by us on an M4.
- Reproduce our evals: `jev-style eval synth/v2/p_eval.jsonl` and compare with the 0.8B numbers above.
- pplx-27b has no MLX build and needs ~15 GB even at 4-bit; skip it on the laptop.
- Mac MLX results do not predict AWS CPU latency; benchmark the Linux container separately.
