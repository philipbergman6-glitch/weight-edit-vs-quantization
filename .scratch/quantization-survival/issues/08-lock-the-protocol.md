# Lock the protocol: settings, baselines, scoring, minimum run

Type: grilling
Status: resolved
Blocked by: 02, 03, 07, 09
Map: [does the edit survive quantization?](../map.md)

## Question

Decide, with Philip, everything the run needs:

- Token limit (MIT used 32,768) given the time budget from the speed test.
- Sampler settings and seed, identical for every version; one response per question or several.
- Which questions: source, how many, how chosen.
- Exactly what 8-bit and 4-bit mean in the chosen tool.
- The two baselines on the base model: how thinking is turned off; which repetition penalty value.
- How a response is scored as looping, and how accuracy is graded.
- Which token-limit measure the table reports: MIT's (any response cut at the limit) or the glossary's looping (cut at the limit with no final answer), or both.
- What the second baseline is, given MIT's settings already include presence penalty 1.5.
- How uncertainty is reported with the numbers.
- The guaranteed minimum run: the smallest run that still answers the question and is certain to finish by Sat 2026-11-14, and the order in which runs happen so the most important rows finish first.

Resolved when the spec can be written with nothing left to choose.

## Answer

Resolved 2026-11-12 with Philip (yes to all six recommendations).

- **Token limit and questions:** 32,768 new tokens (MIT's). 200 questions are drawn, stratified by subject and level with a fixed seed, and split into two balanced halves of 100. Half A runs on every row first; half B runs only if time allows. The id lists are committed before the first run.
- **Order and guaranteed minimum:** 16-bit pair, then 4-bit pair, then 8-bit pair, then the two baselines. The six versions on half A are the guaranteed minimum.
- **Settings, identical for every version:** temperature 0.6, top-p 0.95, top-k 20, min-p 0, presence penalty 1.5, frequency penalty 0, repeat penalty 1.0, seed 0, thinking on, one response per question, prompt = problem + newline + "Please reason step by step, and put your final answer within \boxed{}.", no system prompt. llama.cpp traps fixed: sampler order penalties, temperature, top-k, top-p; penalty window covers the whole context (34,816).
- **Precision levels:** BF16 (16.01 bits per weight), Q8_0 (8.52), stock Q4_K_M (5.51 on average), as built in ticket 07.
- **Looping:** the main number is the share of responses that hit the token limit (`finish_reason == "length"`), as MIT and TurinTech report it. The stricter "hit the limit and gave no final boxed answer" is recorded beside it. Glossary updated.
- **Baselines, base model at BF16:** (a) thinking off, everything else identical; (b) thinking on with llama.cpp repeat penalty 1.1 added.
- **Grading:** last `\boxed{}` after the last `</think>`, checked with math-verify 0.9.0, gold first.
- **Uncertainty:** Wilson 95% interval per rate; exact McNemar test for base vs edited at each level; paired bootstrap for the "survives" ratio.
- **Machine:** plugged in, kept awake, mostly unused; 8 parallel streams.
