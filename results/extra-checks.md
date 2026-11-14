# Extra checks

Run after the table was seen; not part of the plan agreed before the run. Produced by `python -m wevq.extra`.
Questions: 100. p-values are exact McNemar, two-sided, not corrected for the number of checks.

## Paired comparisons

| A | B | Measure | Only A | Only B | p |
|---|---|---|---|---|---|
| edited-BF16 | edited-Q8_0 | looping | 7 | 19 | 0.029 |
| edited-BF16 | edited-Q8_0 | correct | 16 | 0 | 3.1e-05 |
| edited-BF16 | edited-Q4_K_M | looping | 14 | 12 | 0.85 |
| edited-BF16 | edited-Q4_K_M | correct | 21 | 2 | 6.6e-05 |
| edited-Q8_0 | edited-Q4_K_M | looping | 23 | 9 | 0.02 |
| edited-Q8_0 | edited-Q4_K_M | correct | 11 | 8 | 0.65 |
| edited-BF16 | baseline-thinking-off | looping | 17 | 13 | 0.58 |
| edited-BF16 | baseline-thinking-off | correct | 17 | 5 | 0.017 |
| base-BF16 | baseline-thinking-off | looping | 61 | 0 | 8.7e-19 |
| base-BF16 | baseline-thinking-off | correct | 1 | 36 | 5.5e-10 |
| base-BF16 | baseline-repeat-penalty | looping | 17 | 3 | 0.0026 |
| base-BF16 | baseline-repeat-penalty | correct | 3 | 14 | 0.013 |

## Accuracy among responses that did not loop

| Row | Did not loop | Of those, correct | Looped but correct |
|---|---|---|---|
| base-BF16 | 12 | 12 (100%) | 2 |
| edited-BF16 | 69 | 61 (88%) | 0 |
| base-Q8_0 | 15 | 15 (100%) | 0 |
| edited-Q8_0 | 57 | 44 (77%) | 1 |
| base-Q4_K_M | 16 | 16 (100%) | 0 |
| edited-Q4_K_M | 71 | 41 (58%) | 1 |
| baseline-thinking-off | 73 | 47 (64%) | 2 |
| baseline-repeat-penalty | 26 | 25 (96%) | 0 |
