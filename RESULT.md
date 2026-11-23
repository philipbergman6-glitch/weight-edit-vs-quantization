# Result: the edit survives quantization, but accuracy drops

Run finished Sat 2026-11-14, 03:50 IST. Every number measured here comes from [`results/table.md`](results/table.md),
[`results/extra-checks.md`](results/extra-checks.md), [`results/speed.md`](results/speed.md),
[`results/controls.md`](results/controls.md) or [`results/edit-rounding.md`](results/edit-rounding.md).
Numbers from other people's work are named with their source.

## The question

MIT's published weight edit makes Qwen3.5-0.8B loop far less on maths questions at full precision.
Does that still hold when the base model and the edited model are quantized to 8-bit and to a stock 4-bit file?

## Answer

Yes for looping, at both levels. No for accuracy: the edited model answers fewer questions correctly once quantized.

| Version | Looping | Accuracy |
|---|---|---|
| base, full precision (16-bit) | 88% (80-93) | 14% (9-22) |
| edited, full precision (16-bit) | 31% (23-41) | 61% (51-70) |
| base, 8-bit | 85% (77-91) | 15% (9-23) |
| edited, 8-bit | 43% (34-53) | 45% (36-55) |
| base, 4-bit (Q4_K_M) | 84% (76-90) | 16% (10-24) |
| edited, 4-bit (Q4_K_M) | 29% (21-39) | 42% (33-52) |
| base, thinking off (baseline) | 27% (19-36) | 49% (39-59) |
| base, repetition penalty 1.1 (baseline) | 74% (65-82) | 25% (18-34) |

100 MATH-500 questions, one response each. Looping = the response hit the 32,768-token limit. Brackets are 95% intervals.

| Precision level | Reduction in looping | Share of the full-precision reduction kept | Verdict |
|---|---|---|---|
| full precision | 57 points | reference (valid: p = 1.4e-17) | |
| 8-bit | 42 points | 0.74 (0.57-0.93) | survives |
| 4-bit | 55 points | 0.96 (0.77-1.20) | survives |

## What the numbers say

1. **The edit works on this setup.** At full precision looping falls from 88% to 31%. MIT report 93.0% to 33.1%.
2. **The reduction in looping survives both precision levels.** Both intervals lie above the 0.5 bar.
3. **Accuracy does not fully survive.** The edited model goes from 61% correct to 45% at 8-bit and 42% at 4-bit.
   Paired: at 8-bit it lost 16 questions and gained none; at 4-bit it lost 21 and gained 2 (extra check).
4. **At 4-bit the edited model stops looping but is wrong more often.** Of its responses that ended on their own,
   88% were correct at full precision, 77% at 8-bit and 58% at 4-bit (extra check).
   The two levels lose answers in different ways (extra check): at 8-bit, 14 of the 16 lost answers hit the token limit
   (median response length rose from 22,643 to 28,400 tokens); at 4-bit, 9 of the 21 did and 12 ended with a wrong or missing answer.
5. **The base model hardly changes** across precision levels: 84-88% looping, 14-16% accuracy.
6. **Turning thinking off gets a similar drop in looping without any edit** (27% against 31%), but fewer correct answers
   (49% against 61%; paired p = 0.017, extra check). A repetition penalty of 1.1 helps only a little.

## Prediction against outcome

The prediction was committed before the first run ([`PREDICTION.md`](PREDICTION.md), commit `9e5f6ec`).

| Prediction | Outcome |
|---|---|
| 8-bit survives, keeping at least half, if not three-quarters | Right: kept 0.74 |
| 8-bit answers somewhat fewer questions | Right in direction; the drop was larger: 61% to 45% |
| 4-bit does not survive | Wrong: kept 0.96 |
| 4-bit answers many fewer questions | Right: 61% to 42% |
| Reason: rounding erases the edit itself, not the whole model | Not supported: the edit's effect on looping stayed; correct answers are what dropped. Read back from the files, the 8-bit edit is intact (direction cosine 0.9998) and the 4-bit edit is bent but mostly there (0.93 and 0.90) ([`results/edit-rounding.md`](results/edit-rounding.md), post-hoc) |

## Limits

- **Small sample.** 100 questions, one response each. Intervals are about plus or minus 10 points. MIT used 500 questions with 4 responses each.
- **8-bit kept less than 4-bit, and I cannot explain it.** The edited model looped more at 8-bit than at full precision
  (19 questions against 7, p = 0.03, extra check, not corrected for the number of checks). With one response per question, chance is a live explanation.
- **Accuracy is higher than MIT's** (61% against their 48.1% for the edited model; 14% against 7.9% for the base model). The cause is not established;
  candidates are the smaller sample and llama.cpp against their vLLM setup. The full-precision rows are a sanity check, not a replication.
- **One 4-bit recipe, one tool.** Stock llama.cpp Q4_K_M, which averages 5.51 bits per weight. Other recipes and tools were not tested.
- **One sampler.** Every row used the published sampler (temperature 0.6, presence penalty 1.5; `results/table.md`, Settings),
  so "survives quantization" holds under that sampler only. One evaluator, the author of a competing edit, reports that with greedy
  decoding and no presence penalty the edit scores 5% with 95% of answers at the 32K limit, against 52% and 28% with the published
  sampler (Nondual-Observer, discussion #5 on the edited model's Hugging Face page). Single source; not re-run here.
- **One model, one edit, one benchmark.**
- **Extra checks** were chosen after seeing the table. They are labelled as such and should be read as leads.
- **Why accuracy drops is not measured here.** This run shows that it drops, not the mechanism. One cause is ruled out at 8-bit:
  the edit survives rounding there almost exactly (`results/edit-rounding.md`), so the 8-bit drop must come from somewhere else
  (rounding of the rest of the model, or chance). The base model scores too low (14-16%) to show an accuracy drop of its own,
  so a control was added after the run (`results/controls.md`, post-hoc): the base model with thinking off, which scores 49%.
  At 8-bit it still scores 49% (14 questions lost, 14 gained, p = 1), while the edited model lost 16 and gained none.
  So at 8-bit, quantization costs the edited model accuracy and not this working model. The two rows differ in more than the edit:
  the edited model also thinks, and its answers are far longer, so long reasoning being more fragile under rounding is a live
  alternative. At 4-bit the control also drops, from 49% to 41% (lost 15, gained 7, p = 0.13), while the edited model drops
  from 61% to 42% (lost 21, gained 2). So at 4-bit compression costs both models some accuracy; the edited model's drop looks larger,
  but with 100 questions this run cannot show that the two drops differ.

## What was already published and what this adds

- Already published: TurinTech tested the edited model at a calibrated 4-bit against full precision (45.20% against 46.95%, same share at the token limit).
  Others reported that thinking off on the base model is competitive with the edit.
- Added here: the base model and the edited model side by side at full precision, 8-bit and stock 4-bit on one setup, with a
  committed prediction, paired tests and the two baselines in the same table. The accuracy drop at stock 4-bit (61% to 42%) is larger than the
  one TurinTech saw with a calibrated 4-bit file; the two runs differ in recipe, sample and setup, so this is a contrast, not a contradiction.

## Hardware

| Precision level | File size | Bits per weight | Speed, one stream |
|---|---|---|---|
| full precision | 1,517 MB | 16.01 | 65 tokens/s |
| 8-bit | 812 MB | 8.52 | 102 tokens/s |
| 4-bit | 529 MB | 5.51 | 123 tokens/s |

Apple M5, 16 GB, llama.cpp 0.9.0, offline. Settings for every row are listed in `results/table.md`.
