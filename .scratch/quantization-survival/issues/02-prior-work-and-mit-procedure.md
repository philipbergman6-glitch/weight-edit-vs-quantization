# Re-check the prior-work claims and MIT's exact test procedure

Type: research
Status: resolved
Blocked by: none
Map: [does the edit survive quantization?](../map.md)

## Question

The README's prior-work section is marked second-hand. Re-check each claim in it against primary sources, starting with the two PDFs in `reading/` (the MIT post and arXiv 2611.09382) and the edited model's Hugging Face page.

1. MIT's exact evaluation procedure for Qwen3.5-0.8B: precision, runtime, sampler, token limit, thinking mode, number of questions, number of runs per question, how a response is counted as looping or failed, how answers are graded, and what "50 forward passes" refers to.
2. What quantization tests of this edit already exist: who, which precision levels, which tool, how many questions, what result. Is "one clean comparison at 200+ questions" still an open gap?
3. The criticisms: thinking off recovers most of the gain; results swing with sampler settings; "ordinary steering". Who said each, with what numbers?
4. The three cited papers (arXiv 2410.16454, 2406.11717, 2606.10154): does each say what the README says it says?

Mark every claim as confirmed, corrected (with the correction) or not found.

## Answer

Resolved 2026-11-12. Full findings with quotes and sources: branch `research/prior-work-and-mit-procedure` (commit `5476380`), file `research/prior-work-and-mit-procedure.md`.

**The README's "still open" claim is no longer true as written.** TurinTech published (2026-11-04) the edited model at BF16 vs their Q4_K_M on all 500 MATH-500 problems x 4 samples, same llama.cpp binary and settings: 46.95% vs 45.20%, with 40.55% of answers reaching the token limit in both. Not covered by them: the base model on MATH-500, any 8-bit version, a stock (uncalibrated) 4-bit file, settings-only baselines. What is still unpublished, as far as the search found: base and edited at full, 8-bit and 4-bit on one stack.

Corrections to the README:

- "4-bit tests on about 40 questions each, mixed results": one such test found (MLX plain 4-bit, 40 problems: 27.5% hit the limit, accuracy 12/40 vs 21/40). The other 40-question test was on 8-bit.
- Arditi et al. (2406.11717) says nothing about quantization; "routinely shipped as 4-bit and still work" has no source there.
- "So it stops repeating itself" is overstated: the edited model still hits the limit on 33.1% of MATH-500 answers (base 93.0%).
- Unlearning paper 21% / 83%: confirmed, but it is an average over methods, and the same paper says 8-bit behaves like full precision.
- Hu et al. is a different group (Shanghai AI Laboratory), makes different edits (layer 23), does not test the released edit and has no quantization experiments.
- 131,072 weights targeted; 130,188 actually differ after bfloat16 rounding.

MIT's procedure: vLLM, bfloat16, text-only export; thinking on; temperature 0.6, top-p 0.95, top-k 20, presence penalty 1.5, seed 0; 32,768 new tokens, context 34,816; prompt = problem + "Please reason step by step, and put your final answer within \boxed{}."; MATH-500 all 500 x 4 samples, score = mean over samples; grader = last `\boxed{}` checked with math-verify 0.9.0; "hit token limit" = share with `finish_reason == "length"`, no loop detector. "50 forward passes" is the editor's search budget, not an evaluation setting.

Design points raised (carried to [Restate what this repo adds](09-restate-what-this-repo-adds.md) and [Lock the protocol](08-lock-the-protocol.md)):

- MIT's token-limit metric counts any response cut at the limit; the glossary's looping adds "without a final answer".
- MIT's settings already include presence penalty 1.5, so the planned repetition-penalty baseline must be something else.
- Thinking-off baseline is already measured by others: base thinking off 45.8% vs edited thinking on 50.2% (500 x 4).
- The edit is not small per weight: the two edited tensors change by 10.6% and 8.1% in relative size.
- Laptop replications used 8K to 16K limits; at 16K about 68% of edited answers still hit the limit, against 33% at 32K.
