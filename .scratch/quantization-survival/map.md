# Map: does the edit survive quantization?

Label: wayfinder:map

## Destination

A locked experiment spec: every setting needed to run the six versions and two baselines is decided and written down, so the build and run can start with nothing left to choose. The spec is then split into build tickets (`/to-spec`, `/to-tickets`); the run, `RESULT.md`, the demo and the spoken version come after this map.

## Notes

- Domain: measuring an ML model on a laptop (Apple M5, 16 GB). Read `README.md`, `CLAUDE.md` and `GLOSSARY.md` first; use the glossary's terms.
- Purpose: a two-minute supporting talking point for Philip's interview on Tue 2026-11-17 (Skapion). Results table due end of Sat 2026-11-14.
- Scope is the core only: six versions plus two baselines. "One question, one table, one demo."
- Philip is learning quantization through this. Explain every decision in plain words.
- `PREDICTION.md` is written by Philip, in his words, and committed before any model generates any text. Never write or edit it for him.
- Hard rule: no ticket before [Philip writes and commits the prediction](issues/06-philip-writes-prediction.md) may make a model generate text. Downloading, hashing and diffing weights is allowed.
- Every number must trace to a file in `results/`. Sampler settings are fixed explicitly and recorded.
- Record per version: file size, memory used, tokens per second (answers the "hardware sizing" interview question).
- Tracker: local markdown, see `docs/agents/issue-tracker.md`.
- Skills: `grilling` and `domain-modeling` for decision tickets; `research` for research tickets; `plain-english` when explaining results.

## Decisions so far

<!-- one line per closed ticket: gist + link -->

- Charting (2026-11-12): destination is a locked spec; tracker is local markdown; looping = reaching the token limit without a final answer, accuracy is the second measure; Philip writes the prediction after a prep session and before any generation.

- [Which tool runs this model at full, 8-bit and 4-bit on this laptop?](issues/01-quantization-toolchain.md): llama.cpp v0.9.0 GGUF for all six versions (BF16, Q8_0, Q4_K_M), sampler order and penalty window set explicitly; commands untested.
- [Re-check the prior-work claims and MIT's exact test procedure](issues/02-prior-work-and-mit-procedure.md): the "still open" claim is out of date (a 500-question BF16 vs 4-bit test of the edited model exists); six README corrections; MIT's full procedure recovered.
- [Where MATH-500 comes from and how answers are graded](issues/03-math-500-source-and-grading.md): `HuggingFaceH4/MATH-500`, last boxed answer checked with math-verify 0.9.0, 200 stratified questions, Wilson intervals and McNemar test.
- [Download both models, record hashes, diff the weights, confirm the edit](issues/04-download-hash-diff.md): both models on disk and hash-verified; stored precision is BF16; the edit is exactly two tensors (layers 15 and 19 `down_proj`, 64 columns each), narrow but large where it lands.
- [Restate what this repo adds](issues/09-restate-what-this-repo-adds.md): base and edited side by side at full, 8-bit and stock 4-bit on one setup; continue; README corrected with Philip's approval; the prediction states the known 4-bit result.

## Not yet specified

- Which question to use in the live demo (needs results: one where the base model loops and the edited one answers at 4-bit, or honestly does not).
- What to report and do if the full-precision check fails (edited model does not loop clearly less than base).
- Shape of `RESULT.md` and of the 45-second spoken version.
- How to split the build and run into tickets once the spec is locked.

## Out of scope

- Sweeping the edit strength: an optional extra in the README, beyond the core table.
- Measuring the edit size against the rounding step: same.
- Re-deriving the edit with another editor model (e.g. Fable 5.2): others have already done this; high risk for the deadline.
