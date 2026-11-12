# Where MATH-500 comes from and how answers are graded

Type: research
Status: resolved
Blocked by: none
Map: [does the edit survive quantization?](../map.md)

## Question

Where is the MATH-500 question set obtained (dataset name, exact source, licence, can it be used fully offline once downloaded)? What fields does it have (subject, difficulty level)? How do standard evaluations extract the final answer from a response and decide it is correct (boxed-answer extraction, normalisation, equivalence checking), and which open implementation is most used? Which grader did the MIT authors use, if stated?

Also: for a 200-question subset, what are sensible ways to choose it (first 200, fixed-seed random, stratified by subject and level), and how wide is the uncertainty on a rate measured on 200 questions?

## Answer

Resolved 2026-11-12. Full findings: branch `research/math-500-source-and-grading` (commit `e3a816d`), file `research/math-500-source-and-grading.md`.

- **Dataset:** `HuggingFaceH4/MATH-500`, split `test`, revision `6e4ed1a2a79af7d8630a6b768ec859cb5af4d3be`. One 447 kB `test.jsonl`, not gated, usable offline. Fields: `problem`, `solution`, `answer`, `subject`, `level`, `unique_id`. No licence declared on the card; the parent dataset was taken down on Hugging Face after a DMCA notice. Suggestion: git-ignore the question file, commit only the id list and its hash.
- **Grader:** MIT's method: cut the response at the last `</think>`, take the last brace-matched `\boxed{}`, check with `math-verify==0.9.0` (sympy-based, no LLM judge), gold answer first. Never pass a whole looping response to the parser (can take minutes); grade in the main thread. Not yet confirmed to install and run offline on this laptop.
- **MIT's prompt and protocol:** found in their linked repo (`RikiyaT/lm_understand-logs`), matching ticket 02.
- **Subset:** 200 questions stratified by subject and level, fixed seed, id list committed before the first run. Fallback: first 200 in file order.
- **Uncertainty:** Wilson 95% interval per rate (n=200: about +/-4 points near 10% or 90%, +/-7 near 50%); exact McNemar test for paired base-vs-edited comparisons; paired bootstrap for the "survives" ratio. A "survives" ratio near 0.5 would be roughly 0.5 +/- 0.14 on 200 questions, so results near the half-way line cannot be called.
- **Caveat on comparability:** MIT's 7.9% and 48.1% are 4-sample means over 500 questions at a 32,768 limit; a single-sample 200-question run is not the same estimate.
