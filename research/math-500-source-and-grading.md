# MATH-500: where it comes from and how answers are graded

Research for ticket `.scratch/quantization-survival/issues/03-math-500-source-and-grading.md`.
Date: 2026-11-12. No model was run and no weights were downloaded for this note.

Labels used below: **[observed]** = read directly in the cited source or computed here from the downloaded file;
**[inferred]** = my reasoning from observed facts; **[not confirmed]** = could not be checked.

## Recommendations

### 1. Dataset: `HuggingFaceH4/MATH-500`, file `test.jsonl`, pinned

- Use Hugging Face dataset `HuggingFaceH4/MATH-500`, split `test`, revision `6e4ed1a2a79af7d8630a6b768ec859cb5af4d3be`.
  This is the id the MIT authors' own code loads (`load_dataset("HuggingFaceH4/MATH-500", split="test")`).
- It is one 446,564-byte JSON-lines file, not gated. Download it once, record its sha256
  (`35dc41080a3680858b27fa7e0533d2d547825316fc5dafe5d316f4ccc5a06132`, computed here), and read it with plain
  `json`. No `datasets` library and no network are needed afterwards.
- Licence is unclear (no licence on the dataset card; parent dataset taken down from its original Hugging Face
  location after a copyright notice). [inferred] Keep the question file out of the public repo (git-ignore it) and
  commit only the `unique_id` list and the hash. This is caution, not legal advice.

### 2. Grader: the MIT authors' method (last `\boxed{}` + math-verify 0.9.0), no LLM judge

- Extraction: cut the response at the last `</think>` if present, then take the content of the **last**
  `\boxed{...}` (brace-matched). No closed box = no answer = wrong.
- Equivalence: `math-verify==0.9.0` (Apache-2.0, pure Python, sympy-based):
  `verify(parse("\\boxed{" + gold + "}"), parse("\\boxed{" + pred + "}"))`, gold = the dataset's `answer` field.
- Reason: it is exactly what produced the 7.9% and 48.1% being compared against, it runs offline, and it has no LLM
  judge. Copy the ~60 lines of extraction from the authors' `mathqa.py` (MIT) with attribution.
- Three guards, all from documented failure cases (section 2.4):
  1. Extract the box yourself and pass math-verify only the short `\boxed{pred}` string. Never pass the full
     response: looping output with many boxes can make `parse()` take minutes (issue #91).
  2. Call it from the main thread with a timeout (its timeouts use `signal.alarm`).
  3. Also store the strict string-normalisation verdict (Hendrycks `is_equiv`) per response, as the authors do, so a
     disagreement between the two checkers is visible.

### 3. Subset: 200 questions stratified by subject x level, fixed seed, id list committed

- Proportional allocation over the 35 subject-by-level cells, random pick inside each cell with a fixed seed;
  commit the resulting 200 `unique_id`s before the first run.
- Reason: at n=200 a plain random draw or the first 200 drifts a few points from the full set's mix of difficulty
  (section 4); stratifying removes that drift for about 15 lines of code. Every version answers the same ids.
- Acceptable simpler fallback: first 200 rows in file order (the file is already in random order).

### 4. Uncertainty: Wilson interval per rate, paired analysis for comparisons

- Report every looping rate and accuracy with a 95% Wilson interval. At n=200 that is about ±4 points near 10% or
  90% and ±7 points near 50% (exact numbers in section 5).
- For "edited loops less than base on the same questions": count the two kinds of disagreement and use the exact
  McNemar test; report the difference with a paired interval.
- For the glossary's "survives" rule (a ratio of two reductions): paired bootstrap over questions.
- 200 paired questions detect a looping-rate difference of roughly 4.5 to 14.5 points (80% power), depending on how
  often the two versions disagree; the absolute floor is 6 one-way flips with none the other way (3 points).

### Things the spec should decide (found while researching; outside this ticket's question)

- **"Looping" is not what the authors measured.** Their "Hit token limit (%)" is every response whose finish reason
  is `length`, whether or not an answer was boxed. The glossary's looping is "reaches the token limit without giving
  a final answer". The authors' code notes "a cut response can be correct when its box came before the cap". Record
  both per response (hit limit yes/no; boxed answer found yes/no) so either definition can be reported.
- **The authors' numbers are means over 4 samples per question on all 500 questions**, at temperature 0.6 with a
  32,768-token limit. A single-sample 200-question run is not the same estimate; say so next to the table.
- **Where the box is searched.** The authors cut at the last `</think>`; a response that never closes its thinking
  has no `</think>`, so the whole text is searched. If the local runner returns thinking in a separate field, the
  text handed to the grader must be defined the same way for every version.

---

## 1. Source

### 1.1 What MATH-500 is

[observed] Dataset card of `HuggingFaceH4/MATH-500` (full text of the card body):

> "This dataset contains a subset of 500 problems from the MATH benchmark that OpenAI created in their _Let's Verify
> Step by Step_ paper. See their GitHub repo for the source file:
> https://github.com/openai/prm800k/tree/main?tab=readme-ov-file#math-splits"

Source: https://huggingface.co/datasets/HuggingFaceH4/MATH-500 (raw card:
https://huggingface.co/datasets/HuggingFaceH4/MATH-500/raw/main/README.md).

[observed] Who chose the 500 and how. `openai/prm800k` README, section "MATH Splits", quoting the paper (Lightman
et al., "Let's Verify Step by Step", arXiv 2305.20050):

> "In order to avoid the risk of over-fitting on the 7,500 MATH training problems, we expanded the training set to
> include 4,500 MATH test split problems. We therefore evaluate our models only on the remaining 500 held-out
> problems. We selected these 500 test problems uniformly at random, and we believe they are representative of the
> test set as a whole."

Source: https://github.com/openai/prm800k#math-splits

So: OpenAI chose the 500, uniformly at random, from the 5,000-problem test split of the MATH dataset (Hendrycks et
al., NeurIPS 2021, arXiv 2103.03874). Hugging Face's H4 team re-hosted the file.

[observed] The Hugging Face file is the OpenAI file. I downloaded
`https://huggingface.co/datasets/HuggingFaceH4/MATH-500/resolve/main/test.jsonl` and
`prm800k/math_splits/test.jsonl` (Git LFS object of `openai/prm800k`, branch `main`): both are 446,564 bytes, 500
rows, and every `(unique_id, problem, answer)` matches in the same order.

[observed] Hugging Face API metadata (https://huggingface.co/api/datasets/HuggingFaceH4/MATH-500, fetched
2026-11-12): `"sha":"6e4ed1a2a79af7d8630a6b768ec859cb5af4d3be"`, `"lastModified":"2025-12-15T11:01:40.000Z"`,
`"gated":false`, `"downloads":214381` (last month), files `README.md`, `eval.yaml`, `test.jsonl`.

"Most evaluations use this id": [observed] it is the id in the MIT authors' `evaluate.py`, in the edited model's
card ("MATH-500 (HuggingFaceH4/MATH-500)"), and math-verify's README lists "MATH-500" among its supported
datasets. [inferred] The 214,381 monthly downloads suggest it is the common choice. [not confirmed] I did not survey
other evaluation suites to rank ids by use.

### 1.2 Licence and takedown history

| Item | What the source states | Source |
|---|---|---|
| `HuggingFaceH4/MATH-500` | [observed] No licence. The card metadata has only `task_categories`, `language`, `pretty_name`. Three open, unanswered requests: "MIT License?" (2025-02-18), "Add License Information" (2025-05-07), and a pull request "Add license" (2026-06-26) pointing at the prm800k licence, not merged. | https://huggingface.co/datasets/HuggingFaceH4/MATH-500/discussions |
| `openai/prm800k` (the file's origin) | [observed] "MIT License / Copyright (c) 2023 OpenAI" | https://github.com/openai/prm800k/blob/main/LICENSE |
| `hendrycks/math` (parent, code repo) | [observed] "MIT License / Copyright (c) 2021 Dan Hendrycks". Its README now says: "Download the **MATH dataset here**" linking to `qwedsacf/competition_math`. | https://github.com/hendrycks/math |
| `hendrycks/competition_math` (parent, original Hugging Face location) | [observed] API returns `"disabled": true`, tag `license:mit`. | https://huggingface.co/api/datasets/hendrycks/competition_math |
| Mirrors | [observed] `EleutherAI/hendrycks_math` and `qwedsacf/competition_math` are live (`disabled: false`), both tagged `license: mit`. | https://huggingface.co/api/datasets/EleutherAI/hendrycks_math , https://huggingface.co/api/datasets/qwedsacf/competition_math |

[observed] Takedown. Discussion #5 on `hendrycks/competition_math`, opened 2025-01-15 by Hugging Face staff:

> "We received a DMCA takedown notice from the representatives of Art of Problem Solving [...] alleging that
> materials in this repository uploaded by you infringe their copyright. [...] When we receive a DMCA notice, we are
> required to remove access to the allegedly infringing materials."

Source: https://huggingface.co/datasets/hendrycks/competition_math/discussions/5

[observed] The notice itself (Hugging Face's published copy, filed under 2025-01-02):

> "We've ran a script comparing problems from that dataset to those in Alcumus, and found that over 10,000 of the
> 12,500 problems have a similarity score of 95 or above with basic text matching to current problems in our system"

Source: https://huggingface.co/datasets/huggingface-legal/takedown-notices/blob/main/2025/2025-01-02-AoPS.md

[inferred] Status in plain words: the repositories that carry MATH say MIT, but the company whose problems it
contains disputes that anyone had the right to grant it. The 500-problem subset and several full mirrors remain
online and are in everyday use for evaluation. Using it locally to measure a model is ordinary practice; publishing
the problem text again in this repo is the part to avoid. [not confirmed] Whether any counter-notice was filed or
the dispute was resolved; the discussion is still marked open and I found no first-party resolution.

### 1.3 Offline use

[observed] One file, 446,564 bytes, not gated, direct URL above. [inferred] Once saved it needs nothing but
`json.loads` per line; with the `datasets` library instead, `HF_HUB_OFFLINE=1` forces cache-only use.
Pin the revision in the download URL:
`https://huggingface.co/datasets/HuggingFaceH4/MATH-500/resolve/6e4ed1a2a79af7d8630a6b768ec859cb5af4d3be/test.jsonl`
([not confirmed] I fetched via `main`, which the API reported as that revision at the time; I did not fetch the
pinned URL separately.)

### 1.4 Fields

[observed] From the Hugging Face dataset viewer API and the file:

| Field | Type | Example (row 0) |
|---|---|---|
| `problem` | string | "Convert the point $(0,3)$ in rectangular coordinates to polar coordinates. ..." |
| `solution` | string | worked solution ending in `\boxed{...}` |
| `answer` | string | `\left( 3, \frac{\pi}{2} \right)` |
| `subject` | string, 7 values | `Precalculus` |
| `level` | int, 1 to 5 | `2` |
| `unique_id` | string | `test/precalculus/807.json` |

500 rows, 500 distinct `unique_id`s. The `unique_id` is the path of the problem in the original MATH test split.

### 1.5 Distribution over subject and level

[observed] Computed here from `test.jsonl` (sha256 above):

| Subject | L1 | L2 | L3 | L4 | L5 | Total | Share |
|---|---|---|---|---|---|---|---|
| Algebra | 17 | 21 | 26 | 30 | 30 | 124 | 24.8% |
| Counting & Probability | 2 | 7 | 4 | 13 | 12 | 38 | 7.6% |
| Geometry | 2 | 8 | 8 | 10 | 13 | 41 | 8.2% |
| Intermediate Algebra | 7 | 12 | 19 | 23 | 36 | 97 | 19.4% |
| Number Theory | 5 | 10 | 16 | 19 | 12 | 62 | 12.4% |
| Prealgebra | 7 | 19 | 17 | 20 | 19 | 82 | 16.4% |
| Precalculus | 3 | 13 | 15 | 13 | 12 | 56 | 11.2% |
| **Total** | 43 | 90 | 105 | 128 | 134 | 500 | |
| **Share** | 8.6% | 18.0% | 21.0% | 25.6% | 26.8% | | |

## 2. Grading

### 2.1 The two steps

Every standard grader does two things: (a) **extract** one final answer from the response, (b) decide whether it is
**equivalent** to the reference answer.

(a) Extraction. The original MATH code finds the last `\boxed` (else the last `\fbox`) and walks forward counting
braces until the box closes (`last_boxed_only_string`), then strips the wrapper (`remove_boxed`). If the box never
closes, there is no answer. The prompt therefore has to ask for a boxed answer.

(b) Equivalence, three families:

| Family | How it decides | Typical error |
|---|---|---|
| String normalisation | Clean both strings (remove spaces, `\left`, units, `\$`; `\dfrac` to `\frac`; `0.5` to `\frac{1}{2}`; ...) and compare text | Rejects correct answers written differently (`\frac{1}{2}` vs `0.50`, `x+1` vs `1+x`) |
| Symbolic | Parse both into sympy objects and test equality (numeric, simplify the difference, sets, intervals, matrices) | Parser failures; rare false accepts; can hang |
| LLM judge | Ask a model whether the two answers match | Needs a model call; not offline-deterministic. Excluded here |

### 2.2 Open implementations

| Implementation | Method | Licence | Source files |
|---|---|---|---|
| Hendrycks MATH (original) | last-boxed extraction + string normalisation (`is_equiv` = equality after `_strip_string`) | MIT | https://github.com/hendrycks/math/blob/main/modeling/math_equivalence.py , `modeling/dataset/util.py` (`last_boxed_only_string`), `modeling/eval_math_gpt.py` (`remove_boxed`) |
| lm-evaluation-harness `hendrycks_math` | Copy of the Hendrycks functions (`last_boxed_only_string`, `remove_boxed`, `is_equiv`, `strip_string`) | MIT | https://github.com/EleutherAI/lm-evaluation-harness/blob/main/lm_eval/tasks/hendrycks_math/utils.py |
| OpenAI PRM800K grader | Hendrycks normalisation plus sympy equality: `grader.grade_answer(model_answer, gt_answer)` | MIT | https://github.com/openai/prm800k/blob/main/prm800k/grading/grader.py , https://github.com/openai/prm800k/blob/main/prm800k/grading/math_normalize.py |
| math-verify (Hugging Face) | Regex extraction, LaTeX to sympy via `latex2sympy2_extended` (ANTLR grammar), then string / numeric / symbolic / set / interval / matrix comparison | Apache-2.0 | https://github.com/huggingface/Math-Verify/blob/main/src/math_verify/parser.py , https://github.com/huggingface/Math-Verify/blob/main/src/math_verify/grader.py |
| OpenAI simple-evals `math_eval.py` | LLM judge (`equality_checker: SamplerBase`, `check_equality(...)`) | MIT | https://github.com/openai/simple-evals/blob/main/math_eval.py |
| `HuggingFaceH4/MATH-500` `eval.yaml` (inspect-ai) | LLM judge (`scorers: - name: model_graded_fact`) | n/a | https://huggingface.co/datasets/HuggingFaceH4/MATH-500/blob/main/eval.yaml |

[observed] What each says about its own accuracy:

- PRM800K README: "This grading logic is designed to be conservative and will sometimes reject correct answers,
  though it does so less frequently than the normalization logic from MATH. Our logic might sometimes admit
  incorrect answers, though we've put effort into minimizing this."
- math-verify README: "This evaluator achieves the highest accuracy and most correct scores compared to existing
  evaluators on MATH dataset", with a table: Harness 0.0802, Qwen 0.1288, Math-Verify 0.1328. (Their own claim; the
  model behind those scores is not named in the part of the README I read.)
- MIT authors' `mathqa.py` docstring: "The original MATH checker (hendrycks is_equiv: equality after string
  normalisation, stricter) is reported next to it as accuracy_equiv."

"Most used": [observed] math-verify has 1,204 GitHub stars and is the grader of the MIT authors and of the
independent re-run on the model card; the Hendrycks functions are embedded in lm-evaluation-harness. [not confirmed]
I have no usage counts that rank them.

### 2.3 Why math-verify, pinned to 0.9.0

- Same grader and version as the numbers this project compares against (section 3).
- [observed] PyPI: version 0.9.0, licence "Apache 2.0", `requires_python >=3.10`, one runtime dependency
  `latex2sympy2_extended==1.11.0`. The README recommends naming the ANTLR runtime:
  `pip install math-verify[antlr4_13_2]`. Source: https://pypi.org/pypi/math-verify/json
- [inferred] Offline: it is pure Python on sympy and ANTLR with no network calls in the grading path, so it runs
  offline once installed. [not confirmed] I did not install or run it (out of scope for this ticket); check with the
  network off before the first run.
- No LLM judge.

Usage shape, taken from the authors' code (section 3): wrap both sides in `\boxed{}` before parsing. [observed] A
bare LaTeX string does not parse: math-verify issue #70 shows `parse("\\dfrac{9}{7}")` returns `[]` while
`parse("\\boxed{\\dfrac{9}{7}}")` returns `[9/7, '\\frac{9}{7}']`. The README agrees: "the latex must be placed in
latex environment to be parsable."

### 2.4 Known failure cases of math-verify 0.9.0

All [observed] in the project's own issue tracker (https://github.com/huggingface/Math-Verify/issues); all were
open on 2026-11-12.

| Issue | Failure | Relevance here |
|---|---|---|
| #91 | "unclosed `$$`/`\[` followed by many `\boxed{}` makes parse() take minutes while holding the GIL"; "degenerate generations that repeat `\boxed{answer}` until the token limit"; one real response "took ~42 minutes in a single parse() call" | High: looping output is the subject of this project. Avoided by extracting the last box first and parsing only that short string |
| #55 and authors' note | Timeouts use `signal.alarm`. Authors' `mathqa.py`: "math-verify's timeouts use signal.alarm, which works only in the main thread; elsewhere they raise and the library would silently return 'not equal'." | Grade in the main thread, single process |
| #65 | A nested power tower `parse(...)` "hangs forever despite the timeout functionality" | Rare; put an outer time limit around grading and count a timeout as wrong, logged |
| #102 | `\frac\pi4`, `\sqrt\pi` (no braces) are mangled; "can verify a wrong answer" | False accept or reject on unbraced LaTeX |
| #87 | "verify() returns True for any two equations with no free symbols", e.g. `3 = 4` vs `1 = 2` | False accept; MATH answers are rarely bare equations |
| #85 | A period inside the delimiters (`$\frac{1}{3}.$`) "makes correct answers fail and can make wrong ones pass" | Mostly avoided because only the box content is parsed |
| README FAQ | `verify(gold, answer)` is not symmetric: "Order here is important!" | Always pass gold first |

General limits of any boxed-answer grader: an answer given without a box is wrong; a box that is cut off by the
token limit is no answer; when several boxes exist only the last counts.

[inferred] Cross-check: because the grader can err both ways, store for each response the raw text, the extracted
answer, the math-verify verdict and the Hendrycks `is_equiv` verdict. Rows where the two disagree are the ones to
read by hand.

## 3. What the MIT authors used

### 3.1 The blog post

[observed] The post (PDF copy `reading/sparks-of-weight-space-programming.pdf`, pages 15 to 17, and
https://rikiyat.github.io/blog/weight-space-programming/) states the results and the token limit:

> "With 50 forward passes, MATH-500 rose from 7.9% to 48.1% [...] the last column is the share of MATH-500 answers
> that hit the 32,768-token limit [...] with 50 it fell from 93% to 33%."

The web page's setup panel, as returned by a page fetch (machine summary of the page, not my own reading of the
HTML): "Evaluation: MATH-500, GSM8K and six other benchmarks, thinking on, up to 32,768 tokens", "temperature 0.6,
top-p 0.95, top-k 20, presence penalty 1.5", "4 on MATH-500" samples per problem. These match the repository text
below, which I read directly.

**Prompt format and grader: not stated in the post itself** (the PDF text has no mention of `\boxed`, a grader, or
the prompt wording). They are stated in the authors' linked repository.

### 3.2 The authors' repository (linked from the post)

[observed] `RikiyaT/lm_understand-logs`, `exp8_math/README.md`, section "Setup", bullet "Evaluation":

> "vLLM, the chat template with thinking enabled, the user message = problem + "Please reason step by step, and put
> your final answer within \boxed{}.", temperature 0.6, top_p 0.95, top_k 20, presence penalty 1.5, at most 32,768
> new tokens; the last `\boxed{}` answer is graded with math-verify (`code/mathqa.py`). Samples per problem:
> MATH-500 4, GSM8K 2, [...] Scores are the mean accuracy over all samples. Code: `code/evaluate.py`,
> `code/merge.py`, protocol `think35` in `code/profiles.py`."

Source: https://github.com/RikiyaT/lm_understand-logs/blob/main/exp8_math/README.md

[observed] The code agrees:

- Dataset: `exp8_math/code/evaluate.py` line 63-64:
  `load_dataset("HuggingFaceH4/MATH-500", split="test")`, keeping `unique_id`, `problem`, `answer`.
- Prompt: `mathqa.py`: `INSTRUCTION = "Please reason step by step, and put your final answer within \\boxed{}."` and
  `build_prompt` returns `problem + "\n" + INSTRUCTION`. One user turn, no system prompt, passed through
  `tok.apply_chat_template(..., add_generation_prompt=True, enable_thinking=thinking)` (`evaluate.py` lines 160-161).
  The docstring calls it "the instruction the Qwen3.5 model card recommends for math problems"; the Qwen card does
  say: "**Math Problems**: Include "Please reason step by step, and put your final answer within \boxed{}." in the
  prompt." (https://huggingface.co/Qwen/Qwen3.5-0.8B)
- Sampling: `evaluate.py` lines 36-37:
  `SAMPLING_THINK35 = {"temperature": 0.6, "top_p": 0.95, "top_k": 20, "presence_penalty": 1.5, "max_tokens": 32768, "seed": 0}`;
  `SAMPLES["math500"] = 4`.
- Extraction: `mathqa.py` `answer_text` ("a stray reasoning block cut off (up to the last '</think>')") then
  `last_boxed`: "the last '\\boxed', else the last '\\fbox'; brace matched; an unclosed last box = None", extended
  to `\boxed {..}` and `\boxed 5`. "An empty box = None."
- Grader: `mathqa.py` docstring: "Checker (the reward and every accuracy): math-verify 0.9.0,
  verify(parse('\\boxed{gold}'), parse('\\boxed{pred}'))"; gold for MATH-500 is "its 'answer' field"; timeout 5
  seconds in the main thread.
- Token-limit share: `evaluate.py` line 184 `cut += s.finish_reason == "length"`, reported as `cut_share`. It does
  not look at whether an answer was found. Line 185 separately counts "finished without a \\boxed{} answer".
- Published per-benchmark results: `exp8_math/eval/unedited/merged.json` has `math500` =
  `{'acc': 0.079, 'cut_share': 0.93, 'mean_tokens': 30868.4345, 'problems': 500}`; `eval/p50c/merged.json` has
  `{'acc': 0.481, 'cut_share': 0.3305, 'mean_tokens': 22037.1475, 'problems': 500}`.
- Licence of this code: repository `LICENSE`: "Our scripts (*.py and *.sh files written by us, e.g. harness/,
  exp7_sycophancy/code/, exp8_math/code/): the MIT License". Logs and data: CC BY 4.0.

Caveats on that code, all [observed]:

- The README says the `think35` protocol is "in `code/profiles.py`"; I found the string `think35` only in
  `evaluate.py` (`SAMPLING_THINK35`), not in `profiles.py`.
- The module docstring at the top of `evaluate.py` is stale (it describes "a Qwen3-1.7B checkpoint" with
  `enable_thinking=False`, temperature 0.7, 8,192 tokens). The `think35` branch in `run()` is what the README says
  was used.
- `evaluate.py` and `mathqa.py` import a private package (`weightenv.lmo.tasks...`), so they do not run as
  published. Copy the needed functions; do not expect to run the scripts.

### 3.3 The Hugging Face model card of the edited model

[observed] `RikiyaT/Qwen3.5-0.8B-weight-space-programming` card
(https://huggingface.co/RikiyaT/Qwen3.5-0.8B-weight-space-programming):

> "**Independent re-run of this checkpoint:** full MATH-500, 500 problems × 4 samples = 2,000 generations (43.4M
> generated tokens, 51 min on an H200), with the post's protocol: vLLM, thinking on, temperature 0.6, top_p 0.95,
> top_k 20, presence_penalty 1.5, max 32,768 new tokens, seed 0, last `\boxed{}` graded with math-verify 0.9.0. The
> edited model scored **51.0%**, with **31.6%** of answers hitting the token limit. A 25-problem smoke test of the
> base model gave 5.0%, with 95% hitting the limit."

> "This checkpoint and the re-run above were built by akhaliq with ML Intern on Hugging Face Jobs, 2026-11-02 [...]
> vLLM 0.33.0 / transformers 5.20.2 / math-verify 0.9.0, following `exp8_math/code/evaluate.py` (thinking on,
> `think35` sampling, last-`\boxed{}` grading). One substitution: the post evaluated a text-only export of the
> model, and this checkpoint is the full multimodal release."

> "Re-run (this repo's `eval/`): MATH-500 (HuggingFaceH4/MATH-500), math-verify 0.9.0"

The card's usage snippet uses the same prompt wording, `enable_thinking=True`, and the same sampling parameters.
The repo's `eval/` folder holds `scores_edited_math500.json` (summary: `acc 0.51`, `cut_share 0.316`,
`n_problems 500`, `samples 4`) and `scores_base_math500.json` (`acc 0.05`, `cut_share 0.95`, `n_problems 25`),
plus sample generations.

Note the re-run is by a third party (akhaliq), not the post's authors, and its base-model figure rests on 25
problems.

### 3.4 Summary

| Item | MIT authors |
|---|---|
| Dataset | `HuggingFaceH4/MATH-500`, split `test`, all 500 |
| Prompt | one user message: problem + newline + "Please reason step by step, and put your final answer within \boxed{}."; chat template, thinking on; no system prompt |
| Sampling | temperature 0.6, top_p 0.95, top_k 20, presence penalty 1.5, max 32,768 new tokens, seed 0, 4 samples per problem; engine vLLM, bfloat16 |
| Extraction | text after the last `</think>` (whole text if none); last `\boxed{}`/`\fbox{}`, brace-matched |
| Grader | math-verify 0.9.0, gold and prediction each wrapped in `\boxed{}`; 5 s timeout |
| Score | mean accuracy over all samples |
| "Hit token limit" | share of samples with finish reason `length` |
| Where stated | repository README and code; **not stated** in the blog post text |

## 4. Choosing 200 of the 500

[observed] Computed here from the file (level shares; full set is 8.6 / 18.0 / 21.0 / 25.6 / 26.8%):

| Method | L1 | L2 | L3 | L4 | L5 | Largest subject drift |
|---|---|---|---|---|---|---|
| Full 500 (reference) | 8.6% | 18.0% | 21.0% | 25.6% | 26.8% | |
| First 200 in file order | 10.5% | 22.0% | 20.5% | 22.0% | 25.0% | Intermediate Algebra 21.0% vs 19.4% |
| Simple random 200, seed 0 | 9.0% | 17.0% | 19.5% | 30.5% | 24.0% | Prealgebra 20.5% vs 16.4% |
| Stratified 200 (subject x level, proportional, seed 0) | 9.0% | 18.0% | 21.0% | 25.5% | 26.5% | Number Theory 12.5% vs 12.4% |

(The random and stratified rows are one draw each with Python's `random.Random(0)` after sorting by `unique_id`;
another seed gives other numbers for the random row.)

| Method | For | Against |
|---|---|---|
| First 200 | Simplest; no code; nests (first 100 is inside first 200); the akhaliq re-run used a prefix (25) for its base smoke test | Depends on file order being random. [observed] OpenAI says the 500 were chosen "uniformly at random", and the first 200 look mixed, but nothing states the file order was shuffled. Here it is 4 points light on level 4 and 4 heavy on level 2, i.e. slightly easier than the full set |
| Fixed-seed random | Unbiased by construction; a shuffled order also nests | Same size of drift as above, by chance (here 5 points heavy on level 4) |
| Stratified by subject x level | Matches the full set's mix to within 1 point; removes one source of noise when comparing with the authors' full-500 numbers | About 15 lines of code; some cells are tiny (2 problems), so per-cell results mean nothing; does not nest if the run is later extended |

**Recommendation: stratified by subject x level, proportional allocation, fixed seed, id list committed.** Method
used for the table above: for each of the 35 cells, quota = cell size x 200 / 500; take the whole-number part; give
the remaining places to the cells with the largest fractional parts; sample inside each cell with the seeded
generator after sorting ids. [inferred] The choice matters less than fixing it before the first run and using the
same ids for all six versions and both baselines: the comparisons are paired, so any fixed subset gives a fair
within-project comparison. Stratifying mainly protects the comparison with the authors' full-set numbers.

If the run may be extended to 300 or 500 later, generate one stratified *ordering* instead (or accept first-N of a
seeded shuffle) so that the 200 are a subset of the larger run.

## 5. Uncertainty

All numbers below were computed with the Python standard library (script not committed; formulas and a short
checkable snippet are given).

### 5.1 One rate on 200 questions: Wilson 95% interval

Method: Wilson score interval, z = 1.959964, n = 200, p = k/n.

    centre = (p + z²/(2n)) / (1 + z²/n)
    half   = z · sqrt( p(1−p)/n + z²/(4n²) ) / (1 + z²/n)

With n = 200: z² = 3.8415, z²/n = 0.019207, z²/(2n) = 0.009604, z²/(4n²) = 0.00002401.

| Measured rate | k / n | Wilson 95% interval | Width | Roughly |
|---|---|---|---|---|
| 10% | 20 / 200 | 6.57% to 14.94% | 8.37 points | −3.4 / +4.9 |
| 50% | 100 / 200 | 43.14% to 56.86% | 13.73 points | ±6.9 |
| 90% | 180 / 200 | 85.06% to 93.43% | 8.37 points | −4.9 / +3.4 |
| 7% (authors' base accuracy region) | 14 / 200 | 4.22% to 11.41% | 7.19 points | |
| 33% (authors' edited limit-hit region) | 66 / 200 | 26.86% to 39.78% | 12.93 points | |
| 0% | 0 / 200 | 0% to 1.88% | 1.88 points | |

Worked check for 50%: centre = (0.5 + 0.009604) / 1.019207 = 0.5000;
half = 1.959964 × sqrt(0.25/200 + 0.00002401) / 1.019207 = 1.959964 × 0.035693 / 1.019207 = 0.06864.
Interval 0.5 ± 0.0686 = [0.4314, 0.5686].

Worked check for 10%: centre = (0.1 + 0.009604) / 1.019207 = 0.10754;
half = 1.959964 × sqrt(0.09/200 + 0.00002401) / 1.019207 = 1.959964 × 0.021772 / 1.019207 = 0.04187.
Interval [0.0657, 0.1494].

For comparison, all 500 questions would give widths of 5.27 points (at 10% or 90%) and 8.73 points (at 50%).

What the interval does and does not cover: it treats the 200 questions as a sample of the kind of question in
MATH. With sampling temperature above zero there is also run-to-run variation on the same question (the authors
averaged 4 samples per question); with one sample per question that variation is inside the binomial interval for
the population rate, but a single question's outcome is not stable. Record the seed.

### 5.2 Comparing two versions on the same questions

Each question gives a pair of outcomes (base looped? edited looped?). Lay the 200 questions in a 2x2 table:

| | edited loops | edited does not |
|---|---|---|
| **base loops** | a | **b** |
| **base does not** | **c** | d |

Only the questions where the two versions disagree (b and c) carry information about the difference.
Looping-rate difference = (b − c) / 200.

**Test: exact McNemar.** Under "no difference", each disagreeing question is equally likely to be a b or a c, so b
follows Binomial(b + c, 0.5). Two-sided p = 2 × P(X ≤ min(b, c)), capped at 1. This is the standard test for paired
yes/no outcomes; an unpaired two-proportion test would ignore that the questions are the same and is weaker.

**Interval for the difference.** d = (b − c)/n, standard error = sqrt( (b + c)/n − d² ) / sqrt(n), 95% interval
d ± 1.96 × SE. A paired bootstrap (resample the 200 question ids with replacement, recompute, take the 2.5th and
97.5th percentiles) gives nearly the same answer and extends to quantities with no simple formula.

**The "survives" rule is a ratio**, (base − edited at 4-bit) / (base − edited at full precision) ≥ 0.5, built from
four rates on the same questions. Use the paired bootstrap for it: resample question ids, recompute all four rates
from the resampled questions, compute the ratio, repeat (for example 10,000 times), report the percentile interval
and the share of resamples where the ratio is at least 0.5.

### 5.3 How small a difference 200 pairs can detect

Smallest result that can reach p < 0.05 at all (exact McNemar, no flips the other way):

| b | c | two-sided p |
|---|---|---|
| 5 | 0 | 2 × 0.5⁵ = 0.0625 |
| 6 | 0 | 2 × 0.5⁶ = 0.0312 |

So at least 6 one-way flips with none the other way: 6/200 = **3 points** is the hard floor. With flips both ways
more are needed, for example 10 vs 2 (p = 0.039), 15 vs 5 (p = 0.041), 30 vs 14 (p = 0.023), 40 vs 20 (p = 0.014).

Smallest true difference detected 80% of the time (two-sided 5% level). It depends on ψ, the share of questions on
which the two versions disagree. Normal approximation (Connor 1987):
n = ( z_α·sqrt(ψ) + z_β·sqrt(ψ − d²) )² / d², with z_α = 1.96, z_β = 0.8416, solved for d at n = 200; the last
column is the exact-test power computed over a 0.5-point grid.

| Share of questions where versions disagree (ψ) | Detectable difference, normal approx. | Exact test, smallest grid value with ≥80% power |
|---|---|---|
| 5% | 4.4 points | 4.5 points (power 0.82) |
| 10% | 6.2 points | 6.5 points (0.82) |
| 20% | 8.8 points | 9.5 points (0.84) |
| 30% | 10.8 points | 11.5 points (0.83) |
| 50% | 13.9 points | 14.5 points (0.81) |

If flips only ever go one way (c = 0), exact power at n = 200 is 0.21 for a true 2-point difference, 0.56 for 3,
0.81 for 4, 0.94 for 5.

For contrast, treating the two versions as unrelated samples of 200 each needs 2.80 × sqrt(2p(1−p)/200): 8.4 points
near 10% or 90%, 14.0 points near 50%. Pairing helps most when the versions agree on most questions.

**What this means for the planned comparisons** [inferred]:

- Full precision, base vs edited. If the authors' rates hold (93% vs 33% hitting the limit), the expected table at
  n = 200, assuming the two versions' outcomes are independent, is b ≈ 0.93 × 0.67 × 200 = 124.6 and
  c ≈ 0.07 × 0.33 × 200 = 4.6. Difference 60 points, SE = sqrt((0.6462 − 0.36)/200) = 0.0378, 95% interval about
  ±7.4 points. A difference that size is detected with certainty; 200 questions are far more than enough to show the
  edit reduces looping.
- The harder question is whether the reduction at 4-bit is at least half the reduction at full precision. With each
  reduction known to about ±7 points, a ratio near 0.5 (for example 60 points shrinking to 30) will have a wide
  interval, roughly 0.5 ± 0.14 ([inferred], not simulated: first-order error propagation, treating the two
  reductions as independent; reduction 0.60 with SE 0.0378 and reduction 0.30 with SE 0.0386, so
  SE(ratio) = 0.5 × sqrt((0.0386/0.30)² + (0.0378/0.60)²) = 0.072). A ratio near 1 or near 0 will be clear. The prediction and pass bars should be
  written knowing that outcomes near the 0.5 line cannot be called either way on 200 questions.
- Small accuracy differences between precision levels (a few points) are below what 200 questions can detect unless
  the versions agree on almost every question.

### 5.4 Snippet to check the numbers

```python
import math
z = 1.959963984540054

def wilson(k, n):
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return centre - half, centre + half

def mcnemar_exact(b, c):
    n, k = b + c, min(b, c)
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)

print(wilson(20, 200), wilson(100, 200), wilson(180, 200))
# (0.0657, 0.1494) (0.4314, 0.5686) (0.8506, 0.9343)
print(mcnemar_exact(6, 0), mcnemar_exact(10, 2))   # 0.03125 0.0386
```

## 6. Could not verify

- That `math-verify==0.9.0` installs and grades correctly on this machine (Apple M5, a uv-managed Python) with the
  network off. Not installed here.
- The prompt and grader from the blog post's own text: not stated there. They come from the authors' repository
  README and code, which the post links.
- The blog page's collapsed "Setup" panel was read through an automated page fetch, not by me from the HTML. Its
  contents agree with the repository.
- Whether the order of rows in `test.jsonl` was shuffled by OpenAI (only the selection is stated to be random).
- Whether the AoPS copyright dispute over MATH has been resolved, and what licence, if any, validly covers
  MATH-500. No licence is declared on the dataset card.
- Which grader is "most used" across the field by any count. Stated above is only what I observed: the authors'
  choice, GitHub stars, and where the Hendrycks code is embedded.
- GitHub source links point at branch `main` as of 2026-11-12, not at fixed commits (commit hashes were not
  recorded, except the Hendrycks commit `985bdc16` cited inside the authors' `mathqa.py`).
- The ratio-interval estimate in section 5.3 (0.5 ± 0.14) is a rough hand calculation, not a simulation.

## Sources

Dataset
- `HuggingFaceH4/MATH-500` card and files: https://huggingface.co/datasets/HuggingFaceH4/MATH-500
- API metadata: https://huggingface.co/api/datasets/HuggingFaceH4/MATH-500
- Licence requests: https://huggingface.co/datasets/HuggingFaceH4/MATH-500/discussions (numbers 2, 4, 6)
- `openai/prm800k` README ("MATH Splits", "Answer Grading") and LICENSE: https://github.com/openai/prm800k
- Lightman et al., "Let's Verify Step by Step", arXiv 2305.20050 (quoted via the prm800k README)
- Hendrycks et al., "Measuring Mathematical Problem Solving With the MATH Dataset", arXiv 2103.03874; repo
  https://github.com/hendrycks/math (README, LICENSE)
- Takedown: https://huggingface.co/datasets/hendrycks/competition_math/discussions/5 and
  https://huggingface.co/datasets/huggingface-legal/takedown-notices/blob/main/2025/2025-01-02-AoPS.md
- Mirror status: https://huggingface.co/api/datasets/hendrycks/competition_math ,
  https://huggingface.co/api/datasets/EleutherAI/hendrycks_math ,
  https://huggingface.co/api/datasets/qwedsacf/competition_math

Graders
- Hendrycks: https://github.com/hendrycks/math/blob/main/modeling/math_equivalence.py
- lm-evaluation-harness: https://github.com/EleutherAI/lm-evaluation-harness/blob/main/lm_eval/tasks/hendrycks_math/utils.py
- PRM800K: https://github.com/openai/prm800k/blob/main/prm800k/grading/grader.py
- math-verify: https://github.com/huggingface/Math-Verify (README; `src/math_verify/parser.py`, `grader.py`;
  issues 55, 65, 70, 85, 87, 91, 102); https://pypi.org/pypi/math-verify/json
- simple-evals: https://github.com/openai/simple-evals/blob/main/math_eval.py

MIT authors
- Post: https://rikiyat.github.io/blog/weight-space-programming/ ; PDF copy
  `reading/sparks-of-weight-space-programming.pdf` (git-ignored)
- Logs and code: https://github.com/RikiyaT/lm_understand-logs , files `exp8_math/README.md`,
  `exp8_math/code/evaluate.py`, `exp8_math/code/mathqa.py`, `exp8_math/eval/RESULTS_excerpt.md`,
  `exp8_math/eval/unedited/merged.json`, `exp8_math/eval/p50c/merged.json`, `LICENSE`
- Edited model card and `eval/`: https://huggingface.co/RikiyaT/Qwen3.5-0.8B-weight-space-programming
- Base model card: https://huggingface.co/Qwen/Qwen3.5-0.8B

Statistics
- Wilson, E. B. (1927), "Probable inference, the law of succession, and statistical inference", JASA 22.
- McNemar, Q. (1947), "Note on the sampling error of the difference between correlated proportions or
  percentages", Psychometrika 12.
- Connor, R. J. (1987), "Sample size for testing differences in proportions for the paired-sample design",
  Biometrics 43. (Formulas written from memory of these standard results and checked numerically above against an
  exact computation; the papers themselves were not re-read for this note.)
