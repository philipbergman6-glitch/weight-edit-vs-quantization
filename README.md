# Does a direct weight edit survive quantization?

**Status: set up, nothing run yet (2026-11-12).**

## Credit first

The idea and the edit tested here are not mine.

- **Original work:** Takehi, Teoh, Zhang, Khattab (MIT CSAIL), "Sparks of Weight-Space Programming", blog post, 2 Nov 2026. https://rikiyat.github.io/blog/weight-space-programming/
- **Edited model:** `RikiyaT/Qwen3.5-0.8B-weight-space-programming` (Apache 2.0), base `Qwen/Qwen3.5-0.8B`.
- **Follow-up:** Hu et al., "Exploring Weight-Space Programming", arXiv 2611.09382, 6 Nov 2026.

What they showed: a large model (GPT-6 Astra) read the weights of a small model and changed 131,072 of them (about 0.016%) so it stops repeating itself. No training. MATH-500 went from 7.9% to 48.1%.

## The question this repo asks

A model that runs on private or small hardware is usually quantized: every weight is stored with fewer bits, which adds small rounding errors. The edit is a small, precise change. **Does the fix still work at 8-bit and 4-bit?**

My contribution is the measurement, not the edit.

## Why the answer is not obvious

- Small weight changes can be rounded away. Zhang et al., "Catastrophic Failure of LLM Unlearning via Quantization" (ICLR 2025, arXiv 2410.16454): an unlearned model kept 21% of the "forgotten" knowledge at full precision and 83% after 4-bit quantization.
- Large directional edits are routinely shipped as 4-bit files and reported to still work (refusal-direction removal, Arditi et al. 2024, arXiv 2406.11717).
- A direction can survive while the behaviour does not (arXiv 2606.10154).

## What others already did (so nothing here is over-claimed)

Second-hand: gathered by a research pass on 2026-11-12, not all re-read by me. Re-check before quoting.

- Replicating and re-applying the edit: done many times, byte-for-byte.
- 4-bit tests exist on about 40 questions each, with mixed results (fix holds in one; accuracy drops in another).
- Other editor models have been used (including Claude models).
- Known criticisms: turning "thinking" off reportedly recovers most of the gain with no edit; results swing with sampler settings; some call it ordinary steering.

**Still open, and what this repo adds:** one clean comparison of full precision, 8-bit and 4-bit on a single setup, same settings everywhere, at least 200 questions, with the setting-only baselines included.

## Plan

| # | Step | Output |
|---|---|---|
| 1 | Download base and edited model, record hashes | `models/`, `results/hashes.txt` |
| 2 | Sanity check: diff the weights, confirm where the edit is | `results/diff.md` |
| 3 | Write the prediction and pass bars **before any test run** | `PREDICTION.md`, committed |
| 4 | Build 8-bit and 4-bit versions of both models | six model versions |
| 5 | Baselines on the unedited model: thinking off; repetition penalty | rows in the table |
| 6 | Run the same questions on every version, offline, identical settings | `results/table.md` |
| 7 | One-page write-up: table, prediction vs outcome, limits | `RESULT.md` |

Optional, only if time: sweep the edit strength; measure the edit size against the rounding step.

## Rules for this repo

- Prediction is committed before the first test run. It is never edited afterwards.
- Same sampler settings for every version. Settings are written into the results file.
- Every number in the write-up traces to a file in `results/`.
- A failed or messy result is reported as it is.

## Demo

Wi-Fi off. One maths question to two models side by side: the base model loops, the edited one answers. Then the 4-bit edited version on the same question.
