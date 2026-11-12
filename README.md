# Does a direct weight edit survive quantization?

**Status: both models downloaded and the edit confirmed by a weight diff; no model has been run yet (2026-11-12).**

## Credit first

The idea and the edit tested here are not mine.

- **Original work:** Takehi, Teoh, Zhang, Khattab (MIT CSAIL), "Sparks of Weight-Space Programming", blog post, 2 Nov 2026. https://rikiyat.github.io/blog/weight-space-programming/
- **Edited model:** `RikiyaT/Qwen3.5-0.8B-weight-space-programming` (Apache 2.0), base `Qwen/Qwen3.5-0.8B`.
- **Related work by another group:** Hu et al. (Shanghai AI Laboratory), "Exploring Weight-Space Programming", arXiv 2611.09382, 6 Nov 2026. It reruns the method and makes different edits; it does not test the edit used here and has no quantization experiments.

What they showed: a large model (GPT-6 Astra) read the weights of a small model and changed 131,072 of them (about 0.016%) so it repeats itself far less. No training. On MATH-500, answers that ran into the token limit fell from 93.0% to 33.1%, and accuracy went from 7.9% to 48.1%.

## The question this repo asks

A model that runs on private or small hardware is usually quantized: every weight is stored with fewer bits, which adds small rounding errors. The edit touches very few weights, but changes them strongly (`results/diff.md`). **Does the fix still work at 8-bit and 4-bit?**

My contribution is the measurement, not the edit.

## Why the answer is not obvious

- Small weight changes can be rounded away. Zhang et al., "Catastrophic Failure of LLM Unlearning via Quantization" (ICLR 2025, arXiv 2410.16454): averaged over unlearning methods, models kept 21% of the "forgotten" knowledge at full precision and 83% after 4-bit quantization. The same paper reports that 8-bit models behave like full-precision ones.
- This edit is a different kind of change: one direction removed from two tensors, and large where it lands (62% to 85% of the touched columns' size, `results/diff.md`). Removing a single direction by a weight change is also how refusal-direction removal works (Arditi et al. 2024, arXiv 2406.11717); that paper does not test quantization.
- A direction can survive while the behaviour does not. Kadadekar (arXiv 2606.10154): in quantized models the refusal direction stayed almost unchanged (cosine above 0.97) while refusal fell by 12 to 68 points. That is about built-in refusal, not a weight edit.

## What others already did (so nothing here is over-claimed)

Re-checked against primary sources on 2026-11-12; quotes and links are in `research/prior-work-and-mit-procedure.md` on the branch `research/prior-work-and-mit-procedure`. Third-party numbers below are read from their own pages, not re-run by me.

- Replicating and re-applying the edit: done many times, byte-for-byte.
- **4-bit, 500 questions (TurinTech, 4 Nov 2026):** the edited model at full precision vs their 4-bit file, 500 MATH-500 questions x 4 samples, same llama.cpp setup: 46.95% vs 45.20% accuracy, with 40.55% of answers reaching the token limit in both. Their 4-bit file is calibrated (tuned per tensor), and the base model was not run.
- **4-bit, 40 questions (qxlsz, MLX plain 4-bit):** 27.5% of answers hit the limit, so looping stayed reduced, but it solved 12 questions against 21 at higher precision.
- **8-bit:** most independent llama.cpp replications ran 8-bit files and saw the edit work; none compares 8-bit with full precision on the same setup.
- Other editor models have been used (including Claude models).
- Known criticisms, with numbers: the base model with "thinking" off scores 45.8% against 50.2% for the edited model with thinking on (JonathanColetti, 500 x 4); the same edit scored 55% vs 25% on the same 40 questions depending only on sampler settings (NeoCortex); a plain steering vector along the same direction reaches 50.8% (nathanrs), which is why some call it ordinary steering.

**Still open, and what this repo adds:** the base model and the edited model side by side at full precision, 8-bit and a stock (uncalibrated) 4-bit file, on a single setup with the same settings everywhere, so the reduction in looping is measured at each precision level. At least 200 questions, with the setting-only baselines included. I found no published run of the base model at each precision, no 8-bit comparison and no stock 4-bit test above 40 questions.

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
