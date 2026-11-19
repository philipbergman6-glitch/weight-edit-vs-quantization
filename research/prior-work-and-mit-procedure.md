# Prior work and MIT's exact procedure, re-checked against primary sources

Ticket: `.scratch/quantization-survival/issues/02-prior-work-and-mit-procedure.md`
Checked: 2026-11-12. No model was downloaded or run for this note.

Labels used below:

- **STATED**: the source says it, quoted with location.
- **INFERRED**: my reading of what the source implies. Not a quote.
- **CONFIRMED / CORRECTED / NOT FOUND**: verdict on a README claim.

Page numbers for the blog post refer to the PDF print in `reading/sparks-of-weight-space-programming.pdf` ("Blog PDF p.N"). Page numbers for Hu et al. refer to `reading/exploring-weight-space-programming-arxiv-2611.09382.pdf` ("Hu p.N"). Source IDs like [S3] point to the list at the end.

---

## 1. What changes for us

1. **The "still open" claim in the README is no longer fully true.** A full-precision vs 4-bit comparison of the edited model on all 500 MATH-500 problems, 4 samples each, same runtime and settings, was published on 2026-11-04 by TurinTech [S9]: 46.95% (BF16 GGUF) vs 45.20% (their Q4_K_M), with 40.55% of answers reaching the token limit in both. What it does not have: the base model on MATH-500, an 8-bit version, a stock (uncalibrated) 4-bit file, or settings-only baselines. The gap that remains is narrower: base and edited at all three precision levels in one setup, so that the reduction in looping can be computed per precision level, plus the baselines. See section 4.

2. **Small 4-bit and 8-bit results already exist and point in different directions.** MLX plain 4-bit, 40 problems: looping stayed low (27.5% hit the limit) but accuracy fell from 21/40 to 12/40 [S10]. TurinTech calibrated 4-bit, 500 problems: looping identical, accuracy -1.75 points [S9]. LiteRT int4: looped on short prompts and was rejected, anecdotal [S11]. Most independent llama.cpp replications ran on 8-bit (q8_0) files and saw the edit work [S6, S7]. INFERRED: the 4-bit outcome appears to depend on the quantization method, so the method must be named in our table.

3. **MIT's "hit token limit" is not our glossary's "looping".** MIT counts every answer whose generation stopped because it reached 32,768 new tokens (`finish_reason == "length"`), whether or not it contained an answer [S3]. Our glossary adds "without giving a final answer". Others use a third definition (duplicate 8-gram share > 0.3, alone or combined with the cap) [S7, S13, S14]. Decide which one the table reports, and say so.

4. **llama.cpp default sampling halves the measured effect.** Same edit, same 40 problems, q8_0: 55% with vLLM-style sampling, 25% with llama.cpp defaults [S6]. Two specific causes are named: the penalty window covers only the last 64 tokens by default, and temperature is applied last. The fix used by two independent groups: `repeat_last_n` set to the whole context, sampler order penalties, then top-k, top-p, temperature (TurinTech) or penalties, temperature, top-k, top-p (NeoCortex, HedonismJesse, "vLLM order") [S6, S9, S7]. MLX has the same trap: `presence_context_size` defaults to 20 tokens [S10].

5. **MIT's protocol already includes a presence penalty of 1.5.** The README plans a "repetition penalty" baseline on the base model. Under MIT's settings the base model already runs with presence penalty 1.5 and still hits the limit 93% of the time. The baseline needs to be something different from that (for example llama.cpp's `repeat_penalty`), or it duplicates the main row.

6. **The thinking-off baseline has been measured at 500 problems x 4 samples.** Base model, thinking off, authors' thinking-off settings (temperature 0.7, top-p 0.8, 8,192 tokens): 45.8% on MATH-500, against 50.2% for the edited model with thinking on in the same re-run [S8]. Other reports: 44 to 52% [S5], 43.0% [S5], 43.6% [S5]. Our baseline row is a replication, not a new finding.

7. **The edit is not small per weight.** STATED: the two edited tensors change by 10.6% and 8.1% in relative size [S4]. A third party reports the update as the direction component multiplied by -6, that is reversed and amplified [S5]; two other independent readers also report strength 6 [S6, S16]. INFERRED: this is unlike the unlearning case, where the paper's stated mechanism is that weights barely moved. The "small edit gets rounded away" story in the README is weaker than it reads. I did not verify the factor 6 in the authors' own files.

8. **Cost.** STATED: the edited model's mean answer length at a 32,768 cap is 22,037 tokens and the base model's is 30,868 [S4]. STATED: MLX on an M5 Max generates about 217 tokens per second for this model [S10]. INFERRED: 200 questions x 6 versions x roughly 25,000 tokens is about 30 million tokens, roughly 40 hours at that speed, before baselines, on a faster chip than the project's. Independent replications on laptops used 16,384 or 8,192 caps and 40 to 100 problems [S6, S7, S13, S15]. A lower cap changes the numbers: at 16K about 68% of edited answers still hit the cap, against about 33% at 32K [S14, S6].

9. **Use the right full-precision anchor.** The published checkpoint is bfloat16 (873,436,192 BF16 parameters) [S2]. MIT evaluated with `dtype="bfloat16"` [S3]. "Full precision" here means BF16, not float32.

10. **The Hu et al. paper does not test the released edit.** It reruns the method and produces different edits (layer 23, not layers 15 and 19). It is by a different group (Shanghai AI Laboratory), not the MIT authors. It says nothing about quantization. Do not cite its numbers as numbers for the edited model.

---

## 2. MIT's procedure for Qwen3.5-0.8B (Experiment 8)

Three primary sources agree: the blog's "Setup" box (in the live page, collapsed in the PDF print) [S1], the authors' logs README and code [S3], and the model card [S2].

| Setting | Value | Quote | Location |
|---|---|---|---|
| Runtime | vLLM | "vLLM, the chat template with thinking enabled" | [S3] `exp8_math/README.md`, "Evaluation" bullet. Blog body: NOT STATED (no occurrence of "vLLM") |
| Precision | bfloat16 | "the submitted tensors are cast to bfloat16 and replace the originals"; code: `llm = LLM(model=ckpt, dtype="bfloat16", ...)` | [S3] README and `code/evaluate.py`. Blog body: NOT STATED |
| Quantization | not mentioned | No occurrence of "quantiz", "8-bit", "4-bit" in the blog text or in the authors' README | [S1] full text search; [S3] |
| Model evaluated | text-only export of Qwen3.5-0.8B | "the post evaluated a text-only export of the model, and this checkpoint is the full multimodal release. The language-model tensors are identical (hash-verified)" | [S2] model card, "Reproduction" |
| Thinking mode | on | "Model: Qwen3.5-0.8B, thinking on (24 layers, 0.8 billion weights)" | [S1] Setup box, Experiment 8 |
| Sampler | temperature 0.6, top-p 0.95, top-k 20, presence penalty 1.5 | "Sampling: temperature 0.6, top-p 0.95, top-k 20, presence penalty 1.5." | [S1] Setup box. Code: `SAMPLING_THINK35 = {"temperature": 0.6, "top_p": 0.95, "top_k": 20, "presence_penalty": 1.5, "max_tokens": 32768, "seed": 0}` [S3] |
| Seed | 0 | `"seed": 0` | [S3] `code/evaluate.py`; [S2] "seed 0" |
| Token limit | 32,768 new tokens (thinking plus answer) | "Evaluation: MATH-500, GSM8K and six other benchmarks, thinking on, up to 32,768 tokens." | [S1] Setup box; Blog PDF p.16 |
| Context length | 34,816 | `max_model_len=sampling["max_tokens"] + 2048` | [S3] `code/evaluate.py` |
| Prompt | problem + newline + fixed instruction | `INSTRUCTION = "Please reason step by step, and put your final answer within \\boxed{}."` | [S3] `code/mathqa.py` line 57 |
| Number of questions | MATH-500: 500. GSM8K: 1,319. IFEval: 541 | `"problems": 500`, `"problems": 1319`, `"problems": 541` | [S3] `eval/p50c/merged.json` |
| Runs per question | MATH-500: 4. GSM8K: 2. IFEval: 2 | "Each score averages several samples per problem: 16 on AMC23, 4 on MATH-500, Minerva Math, OlympiadBench and GPQA Diamond, 2 on GSM8K and IFEval, and 1 on MMLU-Pro" | [S1] Setup box |
| Score | mean over all samples, not best-of | "Scores are the mean accuracy over all samples." | [S3] README |
| Grader | last `\boxed{}` answer, checked with math-verify 0.9.0 | "the last `\boxed{}` answer is graded with math-verify (`code/mathqa.py`)" | [S3] README; [S2] "math-verify 0.9.0" |
| "Hit token limit" | share of generations that ended by reaching the token limit | "the last column is the share of MATH-500 answers that hit the 32,768-token limit"; code: `cut += s.finish_reason == "length"` and `"cut_share": cut / tot` | Blog PDF p.16; [S3] `code/evaluate.py` |
| Failed answer | no special category: a cut-off answer has no boxed answer and is graded wrong | `pred, _ = Q.extract(s.text); good = Q.is_correct(pred, r["answer"])`; separate counter `no_answer_finished` for answers that finished without a box | [S3] `code/evaluate.py`. INFERRED from the code path; the README does not spell it out |
| Loop detection | none in the headline numbers | The headline column is the cut share only. The blog describes looping in words: "When the base model loops, it repeats the same text and rarely reaches an answer" | Blog PDF p.15 |
| "50 forward passes" | the editor's budget of test runs while searching for the edit. Not an evaluation setting | "we allow it to select prompts from the training sets of GSM8K and MATH to perform a budget of forward passes (average batch of 64 sequences, max 512) on, varying the budget across 10, 25 and 50"; "a forward pass: the model answers up to 512 problems, or reads up to 1,024 texts" | Blog PDF p.15; [S1] Setup box |
| Hardware | not stated for the authors' run. The independent re-run on the model card used an NVIDIA H200 | "51 min on an H200" | [S2] |

Results as published (MATH-500 / GSM8K / IFEval / hit token limit on MATH-500), Blog PDF p.16:

| Qwen3.5-0.8B | MATH-500 | GSM8K | IFEval | Hit token limit |
|---|---|---|---|---|
| Base | 7.9 | 13.8 | 21.0 | 93.0 |
| Edited, 10 forward passes | 12.3 | 25.7 | 49.0 | 87.2 |
| Edited, 25 forward passes | 14.1 | 25.1 | 39.9 | 86.4 |
| Edited, 50 forward passes | 48.1 | 67.1 | 62.3 | 33.1 |

The published edited model is the 50-pass row. The "hit token limit" column is MATH-500 only. On GSM8K the edited model's cut share is 7.2% and the base model's is 87.5% [S3] `merged.json`.

Where the sampler comes from. STATED in the authors' code comment: "its model card's thinking-mode benchmark setting" [S3]. STATED on Qwen's card: benchmarks used "top_p=0.95, top_k=20, presence_penalty=1.5" with "temperature=0.6 under the thinking mode" [S17]. The same card recommends different settings for normal use: "Thinking mode for text tasks: temperature=1.0, top_p=0.95, top_k=20, min_p=0.0, presence_penalty=1.5", suggests 81,920 tokens for hard maths, and says "Qwen3.5-0.8B operates in non-thinking mode by default" [S17]. It also carries the loop warning: "In thinking mode, we have observed that when using the recommended sampling parameters, Qwen3.5-0.8B is more prone to entering thinking loops compared to other Qwen3.5 models" [S17].

Independent re-runs of the same protocol at full precision:

| Who | Stack | n | Base | Edited | Hit limit (base / edited) | Source |
|---|---|---|---|---|---|---|
| akhaliq (on the model card) | vLLM 0.33.0, H200 | edited 500 x 4; base 25 x 4 only | 5.0% (smoke test) | 51.0% | 95% / 31.6% | [S2] |
| JonathanColetti | vLLM bf16 | 500 x 4 both | 7.4% | 50.2% | 93% / 32% | [S8] |
| carlostoledo1891 | vLLM 0.33.0 | 500 x 4, base only | 7.2% | not run yet | 93.1% / n.a. | [S5] issue #4 |

---

## 3. Claim-by-claim check of the README

### Credit section

| # | README claim | Verdict | Evidence |
|---|---|---|---|
| C1 | Authors Takehi, Teoh, Zhang, Khattab (MIT CSAIL); title; blog post; 2 Nov 2026 | CONFIRMED | "Rikiya Takehi* MIT CSAIL ... Jayden Teoh* ... Alex Zhang ... Omar Khattab ... PUBLISHED November 2, 2026", Blog PDF p.1 |
| C2 | Edited model `RikiyaT/Qwen3.5-0.8B-weight-space-programming`, Apache 2.0, base `Qwen/Qwen3.5-0.8B` | CONFIRMED | Card front matter: "license: apache-2.0 / base_model: Qwen/Qwen3.5-0.8B" [S2] |
| C3 | "Follow-up: Hu et al., arXiv 2611.09382, 6 Nov 2026" | CONFIRMED, with a caveat | "arXiv:2611.09382v1 [cs.AI] 6 Nov 2026", Hu p.1. Caveat: the authors are from "Shanghai Artificial Intelligence Laboratory, Tongji University, Fudan University" (Hu p.1), not MIT. It is an independent study of the method, not a follow-up by the original team, and it does not evaluate the released edit |
| C4 | "A large model (GPT-6 Astra) read the weights of a small model and changed 131,072 of them (about 0.016%)" | CONFIRMED, with a precision note | "subtracted that direction from 64 output columns in each (131,072 weights)", Blog PDF p.15; "changes only 131,072 of the model's 0.8 billion weights (0.016%)", p.16. Note: "In p50c, 130,188 of the 131,072 touched weights differ from the original after rounding to bfloat16" [S3] README |
| C5 | "so it stops repeating itself" | CORRECTED (overstated) | The edited model still hits the limit on 33.1% of MATH-500 answers (Blog PDF p.16). The card says "The edited one mostly doesn't" [S2]. Say "loops much less", not "stops" |
| C6 | "No training." | CONFIRMED | "Astra edits the weights in a Python kernel, with no training", Blog PDF p.3; "no training or gradient information is allowed", p.15. Note: the editor did run the model on practice problems (the forward passes) |
| C7 | "MATH-500 went from 7.9% to 48.1%" | CONFIRMED | "With 50 forward passes, MATH-500 rose from 7.9% to 48.1% and GSM8K from 13.8% to 67.1% ... IFEval ... rose from 21.0% to 62.3%", Blog PDF p.16 |

### "Why the answer is not obvious"

| # | README claim | Verdict | Evidence |
|---|---|---|---|
| P1 | Zhang et al., "Catastrophic Failure of LLM Unlearning via Quantization", ICLR 2025, arXiv 2410.16454 | CONFIRMED | arXiv comment field: "ICLR 2025"; first author Zhiwei Zhang [S18] |
| P2 | "an unlearned model kept 21% of the 'forgotten' knowledge at full precision and 83% after 4-bit quantization" | CONFIRMED, wording needs two qualifiers | "for unlearning methods with utility constraints, the unlearned model retains an average of 21% of the intended forgotten knowledge in full precision, which significantly increases to 83% after 4-bit quantization" [S18] abstract. It is an average over several methods, and only for methods with utility constraints. Not one model |
| P2b | (not in README, relevant to our 8-bit row) | NEW | "We observe that models with 8-bit quantization perform similarly to full-precision models" [S18] section 4.3. The paper's effect appears at 4-bit, not 8-bit |
| P2c | "Small weight changes can be rounded away" as the mechanism | CONFIRMED as the paper's stated hypothesis | "existing methods typically adopt a small learning rate and regularization on the retain set, encouraging minimal changes to model weights during unlearning ... quantization is likely to map the weights of the target LLM and the unlearned LLM to the same values" [S18] section 3. INFERRED: this premise (minimal weight change) does not obviously hold for the MIT edit, see section 1 item 7 |
| P3 | "Large directional edits are routinely shipped as 4-bit files and reported to still work (refusal-direction removal, Arditi et al. 2024, arXiv 2406.11717)" | CORRECTED | The paper supports only the parenthesis. It shows a single refusal direction and removal by weight change: "we find a single direction such that erasing this direction from the model's residual stream activations prevents it from refusing harmful instructions" [S19] abstract; section 4 is "A white-box jailbreak via weight orthogonalization". The full text contains no occurrence of "quantiz", "4-bit" or "GGUF". The claim that such edits are routinely shipped at 4-bit and still work is NOT FOUND in this paper. It is community practice and needs its own source or should be dropped |
| P4 | "A direction can survive while the behaviour does not (arXiv 2606.10154)" | CONFIRMED in substance, attribution and scope need care | Paper: Kadadekar, "Quality Is Not a Safety Proxy Under Quantization", single author, preprint [S20]. Its own measurement: "cosine similarity to the FP16 refusal direction remains above 0.97 in every quantized cell, with no detectable association to the screen at this sample size (r = -0.144, p = 0.673, n = 17)" (section 4.4), while "refusal falls by 12-68 percentage points" in 9 rows (abstract). The sentence closest to the README's wording is a citation of other work: "mechanistic work shows refusal direction is structurally retained under quantization even while behavioral refusal degrades [4, 1]" (related work). Scope: this is about a model's built-in refusal behaviour under quantization, n = 17 cells, not about an edit made to weights |

### "What others already did"

| # | README claim | Verdict | Evidence |
|---|---|---|---|
| O1 | "Replicating and re-applying the edit: done many times, byte-for-byte." | CONFIRMED | Card: "rebuilt with `exp8_math/code/apply_edit.py`, which sha256-verifies every rebuilt tensor against the checkpoint evaluated in the post" [S2]. Issue #4: "I decided the edit from the bytes (two implementations sharing no code) ... the edit is exactly as released (two tensors, sha256 as your card prints)" [S5]. Also hash-checked by JonathanColetti [S8], qxlsz [S10], clavis-systems [S5 issue #8], kyle-chalmers [S13] |
| O2 | "4-bit tests exist on about 40 questions each, with mixed results (fix holds in one; accuracy drops in another)." | CORRECTED | I found one 40-question 4-bit test, not two, and both halves of the "mixed result" come from it: "Plain 4-bit quantization did not preserve quality. On the same 40 problems it hit the limit on 27.5%, so loops stayed reduced, but it solved 12 against 21 for this model" [S10]. The other 40-question llama.cpp test (NeoCortex) ran on 8-bit, not 4-bit: "one laptop GPU (8 GB) via llama.cpp (q8_0 GGUF)" [S6]. And a much larger 4-bit test exists, see O2b |
| O2b | (missing from README) | NEW | TurinTech, 500 problems x 4 samples, llama.cpp, same binary and settings for both files: Q4_K_M 45.20% (904/2,000) vs edited BF16 46.95% (939/2,000); reached the limit 811/2,000 in both; "The difference is -1.75 points. A paired bootstrap ... chosen after the run, gives a 95% interval of -3.75 to 0.25 points; it is not a test of equivalence" [S9]. Limits stated by them: "The file is a per-tensor mix of standard llama.cpp quant types, quantized with calibration data, so its Q4_K_M label is a size class"; the unedited model "did not run MATH-500 here" [S9] |
| O2c | (missing from README) other quantized data points | NEW | 8-bit, n = 50, 16K cap, no presence penalty, q8_0 for all cells: base model 2% correct and 100% at cap; edited 36% and 64% [S7]. 8-bit, n = 140, 32K: edited 80/140 [S6]. LiteRT: int8 file published; "An int4 build (blockwise-64 weights) was produced and rejected: it looped on the translation prompt and in the 17 x 23 thought. It is not published" [S11]. ONNX int4 and GGUF Q4_K_M files exist with no evaluation: "No evaluation or independent quality claims are made for this conversion" [S12] |
| O3 | "Other editor models have been used (including Claude models)." | CONFIRMED, results are mixed and mostly on different edits | Read directly: tdotlab, "Here the editor is Claude instead of GPT-6 Astra", own edit at layer 22, 5/100 to 30/100 at a 16K cap on a q8 file [S15]; kyle-chalmers, "gave Claude Code the same kind of task blind ... to see whether it could find its own fix. It didn't" [S13]. Seen only as search results, not read: XLRA (Claude Opus 5.5, code), HomoHabilis, Exorust (Claude Fable 5.1, SQL). Hu et al. used the same editor as MIT: "GPT-6 Astra at maximum reasoning effort", Hu p.10 |
| O4 | "turning 'thinking' off reportedly recovers most of the gain with no edit" | CONFIRMED, now with numbers at scale | JonathanColetti, 500 x 4, vLLM bf16: base thinking off 45.8% vs edited thinking on 50.2%; edited thinking on minus base thinking off "+4.3 [1.9, 6.8]" [S8]. carlostoledo1891, pre-registered, 500 x 4: base with Qwen's non-thinking text settings "45.6% / 51.7%" first sample, "44.0% / 49.8%" all 2,000 [S5]. kristopolous on Hacker News: "if your turn thinking off you get a 52.0% on their evals. That single flag recovers ~72% of their entire claimed improvement" [S21] (uncontrolled; INFERRED: his 72% does not match MATH-500 arithmetic, where 52.0 would exceed the edited 48.1). Qualifiers: the thinking-off number depends on the token cap (36.2% of thinking-off answers hit an 8,192 cap and none of those were correct [S5]); and with thinking off the edit itself costs about 2 points ("Both thinking off: -2.2 [-4.3, -0.1]" [S8]) |
| O5 | "results swing with sampler settings" | CONFIRMED | "The same edit scores 55 % with vLLM-style sampling and 25 % with llama.cpp's default sampling on the same 40 MATH-500 problems. In llama.cpp, set `repeat_last_n` to the full answer length and put temperature before the filters." [S7] discussion #4; report: "The llama.cpp default differs in two ways: the repetition penalty only looks back over the last 64 tokens, and temperature is applied last" [S6]. n = 40, one seed, q8_0. Agreed by a second group: "the edit's measured benefit tracks the decode stack as much as the weights" [S7] discussion #2. Token budget is a second lever: at 16K, edited .34 correct and .68 at cap [S14] |
| O6 | "some call it ordinary steering" | CONFIRMED | Sean Goedecke: "Personally, I would try steering ... This is basically the Heretic abliteration playbook. And this is exactly what Astra did!" [S22]. Hacker News, theptip: "is more of a classic steering vector intervention" [S21]; porridgeraisin: "astra seems to have done h(looping) - h(loop fixed) and then gotten the usual steering vector" [S21]. Supporting measurement: "A constant steering vector of the same size along the same direction works about as well (50.8 on MATH-500)" [S16]; LocalLLaMA runtime vector, 100 MATH-500 problems, 18 to 46 correct [S23]. The blog itself draws the link: "much like removing a behavior by deleting a single direction from a model's weights [14]", Blog PDF p.15, where [14] is Arditi et al. The Honnibal post named in press coverage was not read |
| O7 | "Still open ... one clean comparison of full precision, 8-bit and 4-bit on a single setup, same settings everywhere, at least 200 questions, with the setting-only baselines included." | CORRECTED | See section 4 |

### Claims in the brief that were to be verified

| Claim | Verdict | Evidence |
|---|---|---|
| Sampler "temperature 0.6, top-p 0.95, top-k 20, presence penalty 1.5" is in the blog | CONFIRMED | Verbatim in the Experiment 8 Setup box of the live page [S1]. It is not visible in the PDF print because the box is collapsed there (Blog PDF p.15 shows only "i Setup") |
| "thinking on, up to 32,768 tokens" | CONFIRMED | [S1] Setup box; Blog PDF p.16 |
| The post does not state numeric precision or mention quantization | CONFIRMED for the post | No match for "quantiz", "precision", "float", "bit", "vLLM" in the post text [S1]. The authors' logs README does state bfloat16 and vLLM [S3] |
| Results 7.9 to 48.1, 13.8 to 67.1, 21.0 to 62.3 | CONFIRMED | Blog PDF p.16 |
| "50 forward passes" | CLARIFIED | It is the editor's search budget, see section 2. Hu et al. use the same budget: "Each search is allocated 50 successful forward-tool requests", Hu p.3 |

---

## 4. Is the open-gap claim still true?

Not as written. What exists, against what the README says is missing:

| README requirement | TurinTech [S9] | qxlsz MLX [S10] | NeoCortex [S6, S7] | Still missing |
|---|---|---|---|---|
| Full precision vs 4-bit, same setup | yes (BF16 GGUF vs calibrated Q4_K_M) | yes (bf16 vs plain 4-bit) | no | a stock, uncalibrated 4-bit file at scale |
| 8-bit in the same comparison | no | no | 8-bit only, no full-precision cell on the same stack | yes |
| At least 200 questions | yes, 500 x 4 | no, 40 x 1 | no, 40 to 140 | covered for edited 4-bit only |
| Base model at each precision level | no | base at bf16 only | base at 8-bit only (n = 40 and n = 50) | yes |
| Settings-only baselines in the same setup | no | no | presence-penalty arm at n = 50 | yes |

STATED facts: one comparison at 500 problems shows the edited model's token-limit share unchanged at 4-bit (811 of 2,000 in both files) and accuracy 1.75 points lower with an interval that includes zero [S9].

INFERRED: the question "does the edited model still loop less after 4-bit quantization" has a published answer for one calibrated 4-bit file, and that answer is yes. What no one has published, as far as I could find, is the six-version table: base and edited at full, 8-bit and 4-bit on one stack, which is what the glossary's "survives" (reduction at a precision level at least half the reduction at full precision) needs. Nor a stock 4-bit result at more than 40 problems, where the one small test saw accuracy drop.

A safe way to state the contribution: "A 500-problem test of one calibrated 4-bit file already shows the loop reduction holds. I add the base model at each precision level, 8-bit, a stock 4-bit file, and the settings-only baselines, all in one setup."

I searched Hugging Face (model search, derivative and quantized-of listings, discussion tabs), the authors' GitHub issues, Hacker News and the web. I cannot rule out results posted on X, Reddit or Discord that these did not surface.

---

## 5. Hu et al. (arXiv 2611.09382): what it adds

- Same protocol as MIT: "Sampling: Temperature 0.6, top-p 0.95, top-k 20, presence penalty 1.5 / Reasoning mode: Thinking enabled / Final evaluation: max_new_tokens = 32,768, seed 0", Hu p.10, Table 3. Precision: "Updates are computed in float32 and stored in bfloat16", Hu p.3.
- Different edits. Their main maths edit changes one column: "modifying only 1,023 parameters yields a 29.45-point improvement", Hu p.1; target "W23, column 507", Hu p.12. Held-out MATH-500 8.35 to 37.80, Hu p.5 Table 2.
- Results vary by run: three searches gave "+29.45, +5.00, and +27.30 percentage points", Hu p.6. "six of the 16 trajectories retain the original weights", Hu p.1.
- Rounding already matters at BF16: "an additive update may be smaller than the BF16 spacing at an entry's magnitude, so the rounded value is unchanged", Hu p.12; for one dense edit "Because most per-entry increments fall below BF16 resolution, 1,037,572 entries change" out of 3.67 million, Hu p.13. INFERRED: this is the same rounding effect the project asks about, one step earlier. It applies to their dense edits, not to the released MIT edit, where 130,188 of 131,072 entries survive BF16 rounding.
- No quantization experiments. No evaluation of `RikiyaT/Qwen3.5-0.8B-weight-space-programming`.

---

## 6. Not verified

- The exact update formula of the released edit (factor 6, sign). Reported by three independent readers [S5, S6, S16]; I did not open the authors' `experiment_history` or recompute it.
- Matthew Honnibal's post and the R&D World article: seen in search results only.
- XLRA, HomoHabilis and Exorust repositories (Claude as editor): seen in search results only.
- The Reddit r/LocalLLaMA thread: not retrieved.
- TurinTech's and qxlsz's numbers are their own reports. I read the cards, not the raw output files.
- Whether a stock llama.cpp Q4_K_M or Q8_0 file of the edited model has been benchmarked anywhere. Not found.
- The arXiv papers were read as abstracts plus the specific sections quoted, not end to end.

---

## Sources

- [S1] Blog post, live page: https://rikiyat.github.io/blog/weight-space-programming/ (fetched 2026-11-12; the Experiment 8 "Setup" box). PDF print: `reading/sparks-of-weight-space-programming.pdf`, 22 pages.
- [S2] Edited model card and repo metadata: https://huggingface.co/RikiyaT/Qwen3.5-0.8B-weight-space-programming (revision `d1671a178705bcab7644806d23c535517f35723b`); `eval/scores_edited_math500.json`, `eval/scores_base_math500.json`.
- [S3] Authors' logs and code: https://github.com/RikiyaT/lm_understand-logs/tree/main/exp8_math (`README.md`, `code/evaluate.py`, `code/profiles.py`, `code/mathqa.py`, `eval/p50c/merged.json`, `eval/unedited/merged.json`).
- [S4] Edit manifest and final answer: `exp8_math/runs/p50c/edit/manifest.json`, `exp8_math/runs/p50c/final_answer.md` in [S3]; mean token counts from the `merged.json` files.
- [S5] Authors' repo issues: #4 https://github.com/RikiyaT/lm_understand-logs/issues/4 (carlostoledo1891, with comments by HedonismJesse and buzzedaldrinx86-creator); #8 https://github.com/RikiyaT/lm_understand-logs/issues/8 (fritzprix, clavis-systems); #11 https://github.com/RikiyaT/lm_understand-logs/issues/11 (fus3r); #5 https://github.com/RikiyaT/lm_understand-logs/issues/5.
- [S6] NeoCortex (Dave Uhlemann), "Knowing Is Not Committing" v0.3: https://github.com/NeoCortex0815/knowing-is-not-committing (README, `report/Knowing_Is_Not_Committing_v0.3.md` sections 2 and 3.1), DOI 10.5281/zenodo.24058693.
- [S7] Model page discussions: #2 https://huggingface.co/RikiyaT/Qwen3.5-0.8B-weight-space-programming/discussions/2 and #4 https://huggingface.co/RikiyaT/Qwen3.5-0.8B-weight-space-programming/discussions/4.
- [S8] JonathanColetti re-run: https://huggingface.co/JonathanColetti/Qwen3.5-0.8B-Astra-WeightEdit ("Independent benchmark").
- [S9] TurinTech 4-bit file and results: https://huggingface.co/turintech/Qwen3.5-0.8B-weight-space-programming-Artemis (`README.md`, `RESULTS.md`).
- [S10] qxlsz MLX conversion: https://huggingface.co/qxlsz/Qwen3.5-0.8B-weight-space-programming-mlx ("Evaluation on MLX", "Why there is no 4-bit version", `docs/ANALYSIS_PLAN.md`).
- [S11] LiteRT int8 conversion: https://huggingface.co/litert-community/Qwen3.5-0.8B-weight-space-programming ("Known limitations").
- [S12] Unevaluated quantized re-uploads: https://huggingface.co/NotCherry/Qwen3.5-0.8B-weight-space-programming-GGUF (Q4_K_M), https://huggingface.co/prithivMLmods/Qwen3.5-0.8B-weight-space-programming-GGUF (Q3 to Q8), https://huggingface.co/tepirale/Qwen3.5-0.8B-wsp-ONNX (int4), https://huggingface.co/mradermacher/Qwen3.5-0.8B-weight-space-programming-GGUF.
- [S13] kyle-chalmers replication: https://github.com/kyle-chalmers/weight-space-programming.
- [S14] Human-AI-Evolution note 1: https://github.com/Human-AI-Evolution/weight-space-notes/blob/main/note-1-carrier-localization.md.
- [S15] tdotlab replication: https://github.com/tdotlab/weight-space-programming (`docs/STATUS.md`).
- [S16] nathanrs, weight-space-lp: https://github.com/nathanrs/weight-space-lp.
- [S17] Base model card: https://huggingface.co/Qwen/Qwen3.5-0.8B.
- [S18] Zhang et al., arXiv 2410.16454v3: https://arxiv.org/abs/2410.16454 (abstract; sections 3 and 4.3 of the HTML version).
- [S19] Arditi et al., arXiv 2406.11717v3: https://arxiv.org/abs/2406.11717 (abstract; full-text search of the HTML version).
- [S20] Kadadekar, arXiv 2606.10154v1: https://arxiv.org/abs/2606.10154 (abstract; related work; section 4.4).
- [S21] Hacker News thread: https://news.ycombinator.com/item?id=50341174 (comments 50349041 kristopolous, 50347259 theptip, 50348410 porridgeraisin, 50347685 yurimo, 50351276 erratum_hunter).
- [S22] Sean Goedecke, "LLMs are not superhuman at reading and writing neural network weights": https://www.seangoedecke.com/llms-are-not-superhuman-at-reading-and-writing-neural-network-weights/.
- [S23] LocalLLaMA steering vector: https://huggingface.co/LocalLLaMA/Qwen3.5-0.8B-anti-loop.
- Hu et al., arXiv 2611.09382v1: `reading/exploring-weight-space-programming-arxiv-2611.09382.pdf`, 21 pages, read in full.
