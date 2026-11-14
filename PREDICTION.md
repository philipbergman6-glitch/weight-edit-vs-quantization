# Prediction (write before any test run, then never edit)

Date and time written: 2026-11-12 18:17 IST

Dictated by Philip, typed by Claude from his words.

## What I expect

At 8-bit, the fix will: survive. The edited model will keep at least half, if not three-quarters, of the reduction in looping it has at 16-bit. It will solve somewhat fewer maths questions than at 16-bit. Confidence: quite confident.

At 4-bit, the fix will: not survive. The edited model will not keep at least half of the reduction in looping, and it will solve many fewer maths questions than at 16-bit. Confidence: medium.

Why I think so (one or two sentences): When we quantize from 16-bit to 8-bit or 4-bit, the number of values a weight can take gets lower and lower: 16 values at 4-bit, 256 at 8-bit, and 65,000 plus at 16-bit. When the edited weights are rounded, many of them will be undone, so the edit goes back to what it was before and the fix stops working. In my opinion rounding erases the edit itself; it does not disturb the whole model.

What I knew when I wrote this: I knew TurinTech's calibrated 4-bit result (46.95% vs 45.20%, same share at the token limit) when I wrote this; I expect a stock 4-bit file to do worse.

## Pass bars

- The experiment is valid if, at full precision, the edited model hits the token limit clearly less often than the base model.
- "Survives" at a given level = the edited model keeps at least half of the full-precision reduction in looping.

## Outcome (fill in after the run; do not change anything above)


Filled in 2026-11-14 04:00 IST, typed by Claude from `results/table.md` (commit `396139d`). 100 questions, one response each.

- **Validity:** passed. At full precision the edited model looped on 31% of questions against 88% for the base model (p = 1.4e-17).
- **8-bit, survives:** right. It kept 0.74 of the reduction in looping (interval 0.57-0.93).
- **8-bit, somewhat fewer questions answered:** right in direction, larger than expected: 61% correct fell to 45%.
- **4-bit, does not survive:** wrong. It kept 0.96 of the reduction (interval 0.77-1.20).
- **4-bit, many fewer questions answered:** right: 61% correct fell to 42%.
- **Reason given (rounding erases the edit itself):** not supported. The edit's effect on looping stayed; correct answers dropped.

Full write-up: `RESULT.md`.
