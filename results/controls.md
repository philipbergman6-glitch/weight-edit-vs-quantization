# Control: the base model with thinking off, quantized

Run after the table was seen (post-hoc); not part of the plan agreed before the run. Produced by `python -m wevq.controls`.
Same questions (half A), same settings and llama.cpp build as every other row; thinking off, as in `baseline-thinking-off`.
p-values are exact McNemar, two-sided, not corrected for the number of checks. Brackets are 95% intervals.

| Row | Questions | Looping | Correct | Correct vs full precision: lost / gained | p |
|---|---|---|---|---|---|
| thinking off, full precision (`baseline-thinking-off`) | 100 | 27.0% (19-36) | 49.0% (39-59) | reference | |
| thinking off, 8-bit | 100 | 23.0% (16-32) | 49.0% (39-59) | 14 / 14 | 1 |
| thinking off, 4-bit (Q4_K_M) | 100 | 19.0% (13-28) | 41.0% (32-51) | 15 / 7 | 0.13 |

## Next to the edited model (correct answers out of 100, full precision → quantized)

| Level | Base, thinking off | Edited, thinking on |
|---|---|---|
| 8-bit | 49 → 49 (lost 14, gained 14, p = 1) | 61 → 45 (lost 16, gained 0, p = 3.1e-05) |
| 4-bit (Q4_K_M) | 49 → 41 (lost 15, gained 7, p = 0.13) | 61 → 42 (lost 21, gained 2, p = 6.6e-05) |
