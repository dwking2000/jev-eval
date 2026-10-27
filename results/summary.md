# Synthetic eval summary

## v1_claude_clean  (966 questions, 394 rows)

| engine | accuracy | Brier | mean top-p |
|---|---|---|---|
| jev-0.8b | 70.8% | 0.405 | 0.67 |
| jev-2b | 76.0% | 0.324 | 0.74 |
| pplx-27b-nf4 | 93.0% | 0.109 | 0.91 |

pplx − jev-0.8b: +22.2 pts  (95% CI +19.2 to +25.5)

pplx − jev-2b: +17.0 pts  (95% CI +14.4 to +19.8)

## v2_claude_dirty  (972 questions, 458 rows)

| engine | accuracy | Brier | mean top-p |
|---|---|---|---|
| jev-0.8b | 79.8% | 0.313 | 0.69 |
| jev-2b | 82.8% | 0.245 | 0.77 |
| pplx-27b-nf4 | 92.4% | 0.113 | 0.91 |

pplx − jev-0.8b: +12.6 pts  (95% CI +9.8 to +15.4)

pplx − jev-2b: +9.6 pts  (95% CI +7.0 to +12.3)

## v3_gemma_dirty  (439 questions, 250 rows)

| engine | accuracy | Brier | mean top-p |
|---|---|---|---|
| jev-0.8b | 72.4% | 0.331 | 0.70 |
| jev-2b | 79.7% | 0.283 | 0.75 |
| pplx-27b-nf4 | 83.8% | 0.226 | 0.85 |

pplx − jev-0.8b: +11.4 pts  (95% CI +6.7 to +16.3)

pplx − jev-2b: +4.1 pts  (95% CI +0.5 to +8.0)

## v4c_claude_tuned  (795 questions, 375 rows)

| engine | accuracy | Brier | mean top-p |
|---|---|---|---|
| jev-0.8b | 77.2% | 0.319 | 0.70 |
| jev-2b | 81.3% | 0.266 | 0.76 |
| pplx-27b-nf4 | 91.3% | 0.125 | 0.90 |

pplx − jev-0.8b: +14.1 pts  (95% CI +10.8 to +17.5)

pplx − jev-2b: +10.1 pts  (95% CI +7.2 to +13.1)

## v4g_gemma_tuned  (655 questions, 373 rows)

| engine | accuracy | Brier | mean top-p |
|---|---|---|---|
| jev-0.8b | 79.1% | 0.295 | 0.72 |
| jev-2b | 80.0% | 0.287 | 0.77 |
| pplx-27b-nf4 | 86.9% | 0.179 | 0.87 |

pplx − jev-0.8b: +7.8 pts  (95% CI +4.1 to +11.3)

pplx − jev-2b: +6.9 pts  (95% CI +3.4 to +10.5)

## Generator-source effect (accuracy, same prompt generation; Claude-written vs Gemma-written)

| engine | v2 Claude | v3 Gemma | gap | v4 Claude | v4 Gemma | gap |
|---|---|---|---|---|---|---|
| jev-2b | 82.8% | 79.7% | +3.1 | 81.3% | 80.0% | +1.3 |
| jev-0.8b | 79.8% | 72.4% | +7.4 | 77.2% | 79.1% | -1.9 |
| pplx-27b-nf4 | 92.4% | 83.8% | +8.6 | 91.3% | 86.9% | +4.5 |

If the Qwen-derived engines gain MORE from Claude-written text than a non-Qwen reference would, the gap column is evidence of source bias. We only have Qwen-derived engines here, so compare gap sizes between engines.

## Ambiguous items (two defensible answers). Good model: still right under either label, but LESS confident.

| set | engine | n | acc (primary) | acc (either) | mean top-p | clean-set mean top-p |
|---|---|---|---|---|---|---|
| v2_amb | jev-0.8b | 161 | 60.2% | 88.2% | 0.61 | 0.69 |
| v2_amb | jev-2b | 161 | 59.6% | 93.8% | 0.68 | 0.77 |
| v2_amb | pplx-27b-nf4 | 161 | 73.9% | 97.5% | 0.83 | 0.91 |
| v3_amb | jev-0.8b | 165 | 49.1% | 77.6% | 0.64 | 0.70 |
| v3_amb | jev-2b | 165 | 48.5% | 76.4% | 0.70 | 0.75 |
| v3_amb | pplx-27b-nf4 | 165 | 54.5% | 80.6% | 0.79 | 0.85 |
| v4c_amb | jev-0.8b | 160 | 59.4% | 92.5% | 0.61 | 0.70 |
| v4c_amb | jev-2b | 160 | 63.1% | 96.2% | 0.68 | 0.76 |
| v4c_amb | pplx-27b-nf4 | 160 | 68.8% | 98.8% | 0.80 | 0.90 |
| v4g_amb | jev-0.8b | 128 | 54.7% | 84.4% | 0.65 | 0.72 |
| v4g_amb | jev-2b | 128 | 52.3% | 82.8% | 0.69 | 0.77 |
| v4g_amb | pplx-27b-nf4 | 128 | 56.2% | 85.9% | 0.79 | 0.87 |