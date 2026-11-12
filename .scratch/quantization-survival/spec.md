# Spec: measure whether the edit survives quantization

Status: ready-for-agent
Map: [does the edit survive quantization?](map.md) (all nine tickets resolved; each decision below links to the ticket that holds its detail)

## Problem Statement

Philip has a base model and an edited model whose edit reduces looping at full precision. He does not know whether that reduction is still there once both models are quantized to 8-bit and to a stock 4-bit file, which is how a small model would be run on private hardware. One published test covers the edited model at a calibrated 4-bit; nobody has published the base model and the edited model side by side at each precision level on one setup. He needs a result he can explain in two minutes in an interview on Tue 2026-11-17, with a prediction committed beforehand and every number traceable to a file.

## Solution

Run the same maths questions, with identical settings, on six versions (base model and edited model at full precision, 8-bit and 4-bit) and on two baselines, on Philip's laptop, offline. For each version report looping, looping without an answer, and accuracy, with uncertainty. From those, compute the reduction in looping at each precision level and whether the edit survives there. Produce one table, a one-page write-up comparing the committed prediction with the outcome, and an offline demo.

## User Stories

1. As Philip, I want the same questions and settings used for every version, so that any difference comes from the edit or the precision level and nothing else.
2. As Philip, I want the full-precision pair run first, so that I know early whether the experiment is valid (the edited model loops clearly less than the base model).
3. As Philip, I want the 4-bit pair run second, so that my boldest prediction is tested even if time runs out.
4. As Philip, I want the six versions on the first 100 questions treated as the guaranteed minimum, so that I have a complete table by Saturday evening.
5. As Philip, I want the second 100 questions and the baselines to run only after the minimum is complete, so that extras never put the core at risk.
6. As Philip, I want a run to be resumable after an interruption, so that a crash, a closed lid or a restart does not cost hours of finished work.
7. As Philip, I want every response saved with its settings, token count and stop reason, so that every number in the table can be traced and re-scored.
8. As Philip, I want looping reported the way the MIT authors report it, so that my full-precision row can be compared with their numbers and with TurinTech's.
9. As Philip, I want the stricter "looping without an answer" recorded beside it, so that I can say how much the two measures differ.
10. As Philip, I want accuracy graded the way the MIT authors graded it, with no LLM judge, so that grading is reproducible offline.
11. As Philip, I want a 95% interval on every rate, so that I do not over-read a difference that 100 questions cannot support.
12. As Philip, I want a paired test of base against edited at each precision level, so that "the edited model loops less" is a tested statement.
13. As Philip, I want a "survives" verdict per precision level with its uncertainty, so that I can compare it directly with my committed prediction.
14. As Philip, I want the thinking-off baseline in the same table, so that I can answer the criticism that turning thinking off gets the same gain without an edit.
15. As Philip, I want a repetition-penalty baseline in the same table, so that I can show what a settings-only change achieves.
16. As Philip, I want file size, bits per weight, memory and speed listed per precision level, so that I can answer hardware-sizing questions with my own measurements.
17. As Philip, I want the exact server command and sampler settings written into the results, so that the known llama.cpp sampler trap is visibly handled.
18. As Philip, I want progress visible while the run is going, so that I know how far it is and whether it will finish in time.
19. As Philip, I want a messy or failed result reported as it is, so that the write-up stays honest.
20. As Philip, I want the write-up to state what was already published and what this run adds, so that I do not over-claim.
21. As Philip, I want one question chosen for a live offline demo after the results are in, so that I can show the base model looping and the edited model answering, then the 4-bit edited version.
22. As an interviewer, I want to see the prediction commit dated before the first run, so that I can trust the result was not fitted afterwards.

## Implementation Decisions

**Versions and rows** ([Speed test, with file size and memory per version](issues/07-speed-and-size-test.md), [Lock the protocol](issues/08-lock-the-protocol.md))

- Six versions, already built as GGUF files: base model and edited model at BF16 (16.01 bits per weight), Q8_0 (8.52) and stock Q4_K_M (5.51 on average; the two edited tensors are stored at its lower tier).
- Two baselines on the base model at BF16: (a) thinking off, everything else identical; (b) thinking on with llama.cpp repeat penalty 1.1 added.
- Run order: BF16 pair, Q4_K_M pair, Q8_0 pair, then baseline (a), then baseline (b). Within a pair, base and edited each complete half A before anything runs half B.

**Questions** ([Where MATH-500 comes from and how answers are graded](issues/03-math-500-source-and-grading.md))

- Source: `HuggingFaceH4/MATH-500`, split `test`, at the revision recorded in the ticket. The question file is downloaded once, hash-recorded and git-ignored.
- 200 questions drawn stratified by subject and level with a fixed seed, then split into two halves of 100 (A and B), each stratified the same way. The id lists and the seed are committed before the first run.

**Generation settings, identical for every version** ([Re-check the prior-work claims and MIT's exact test procedure](issues/02-prior-work-and-mit-procedure.md), [Which tool runs this model](issues/01-quantization-toolchain.md))

- Runtime: llama.cpp 0.9.0 `llama-server`, offline, all layers on the GPU, 8 parallel streams, 34,816-token context per stream, no context shift, prompt caching off.
- Prompt: one user message, the problem, a newline, then "Please reason step by step, and put your final answer within \boxed{}." No system prompt. Thinking on (set explicitly on the server and in each request).
- Sampling: temperature 0.6, top-k 20, top-p 0.95, min-p 0, presence penalty 1.5, frequency penalty 0, repeat penalty 1.0, seed 0, sampler order penalties, temperature, top-k, top-p, penalty window 34,816 tokens. One response per question, at most 32,768 new tokens.
- The settings are sent in every request as well as on the server command line, and both are written into the results.

**Two modules**

- **Runner:** given a version, a question list and the settings, produces one record per question and appends it to that version's results file as soon as it finishes. A record holds the question id, the full response text (thinking and answer), the number of generated tokens, the stop reason, the timings and the settings used. Before starting it reads the existing file and skips questions already done, so it is resumable. It fails hard if the server reports settings different from the requested ones, if a request errors, or if a record is malformed. It keeps the laptop awake while running.
- **Scorer:** given the records and the gold answers, produces the per-response flags and the table. It never calls a model. Flags per response: looping (stop reason is the token limit), has a final boxed answer, looping without an answer, correct. A response cut at the limit is graded like any other: whatever last boxed answer it contains is checked.

**Scoring** ([Lock the protocol](issues/08-lock-the-protocol.md))

- Final answer: the text after the last `</think>` (the whole text if thinking never closes), last brace-matched `\boxed{}`.
- Correctness: math-verify 0.9.0, gold answer first, only the extracted boxed strings passed to the parser, graded in the main thread.
- Per version: looping rate, looping-without-an-answer rate and accuracy, each with a Wilson 95% interval, plus mean generated tokens.
- Per precision level: reduction in looping (base minus edited), exact McNemar test on the paired looping flags, and the survives ratio (reduction at that level divided by reduction at BF16) with a paired bootstrap interval over questions. The verdict is "survives" when the ratio is at least 0.5, and is marked "cannot be called" when the interval straddles 0.5.
- Validity check, from the committed pass bar: at BF16 the edited model must loop clearly less than the base model (McNemar p below 0.05). If it does not, the write-up says so and the survives verdicts are not reported.

**Outputs**

- Raw records per version: large, git-ignored.
- Committed: the question id lists, the per-response flags without response text, the table, the run settings, and the hardware numbers from the speed test.
- The write-up and `PREDICTION.md`'s Outcome section are filled in after the table exists. Nothing above the Outcome heading is changed.

## Testing Decisions

- A good test here checks what goes in and what comes out of a module, using recorded text, and never needs a model.
- **Scorer:** tested with a small set of hand-written responses covering: a normal answer after closed thinking; several boxed answers (the last wins); nested braces; no boxed answer; thinking never closed; a response cut at the token limit with and without an earlier boxed answer; an equivalent but differently written answer (for example a fraction and its decimal). Expected flags are written by hand.
- **Statistics:** the Wilson interval and the exact McNemar p-value are tested against the worked values in the grading research note.
- **Question selection:** tested for determinism (same seed, same ids), for the two halves being disjoint and 100 each, and for each half matching the full set's level mix within a few points.
- **Runner:** tested by a two-question smoke run against the real server on the smallest file, checking the record shape, the stop reason, that the server-reported settings match, and that a second invocation skips both questions.
- There is no prior test code in this repo; these are the first tests.

## Out of Scope

- Sweeping the edit strength.
- Measuring the edit size against the rounding step.
- Re-deriving the edit with another editor model.
- Other benchmarks (GSM8K, IFEval), other quantization tools (MLX, bitsandbytes), calibrated or other 4-bit recipes, precision levels below 4-bit.
- More than one response per question.

## Further Notes

- Time budget from the speed test: roughly 3 to 4 hours per row for 100 questions in the worst case, about 20 to 30 hours for all eight rows on half A. Speeds were measured over the first 8,192 tokens only, so long responses may be slower.
- With 100 questions a rate near 50% has an interval of about plus or minus 10 points. A survives ratio near 0.5 will not be callable; the write-up must say so if that happens.
- MIT's published numbers are 4-sample means over 500 questions on vLLM; this run is one sample over 100 to 200 questions on llama.cpp. The full-precision row is a sanity check against theirs, not a replication.
- Known result going in: TurinTech's calibrated 4-bit file scored 45.20% against 46.95% with the same share at the token limit. The committed prediction states this was known.
- After the table: choose the demo question, write `RESULT.md`, fill the Outcome section, and prepare the 45-second spoken version.
