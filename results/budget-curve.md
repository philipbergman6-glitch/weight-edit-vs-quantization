# Correct answers by token budget

Post-hoc, added after the table was seen. Produced by `python -m wevq.budget`. Edited model, one response per question,
100 questions. A question counts at a budget when its response is correct and no longer than that budget.

## Up to the original 32,768-token limit

| Token budget | edited-BF16 | edited-Q8_0 | Gap |
|---|---|---|---|
| 4,000 | 11 | 10 | 1 |
| 8,000 | 17 | 16 | 1 |
| 12,000 | 26 | 24 | 2 |
| 16,000 | 33 | 27 | 6 |
| 20,000 | 43 | 34 | 9 |
| 24,000 | 50 | 38 | 12 |
| 28,000 | 58 | 40 | 18 |
| 32,768 | 61 | 45 | 16 |

Still at the limit: edited-BF16 31, edited-Q8_0 43.

## Responses that hit the limit, continued to 65,536 tokens

| Token budget | edited-BF16 | edited-Q8_0 | Gap |
|---|---|---|---|
| 4,000 | 11 | 10 | 1 |
| 8,000 | 17 | 16 | 1 |
| 12,000 | 26 | 24 | 2 |
| 16,000 | 33 | 27 | 6 |
| 20,000 | 43 | 34 | 9 |
| 24,000 | 50 | 38 | 12 |
| 28,000 | 58 | 40 | 18 |
| 32,768 | 61 | 44 | 17 |
| 40,000 | 64 | 45 | 19 |
| 48,000 | 66 | 48 | 18 |
| 56,000 | 66 | 48 | 18 |
| 65,536 | 66 | 49 | 17 |

Still at the limit: edited-BF16 22, edited-Q8_0 33.

Same question, both rows, at 65,536 tokens: right only at edited-BF16 17, right only at edited-Q8_0 0.
Of the 17 right only at edited-BF16: edited-Q8_0 was still at the limit on 12 and finished with a wrong answer on 5.

Already stuck repeating at 32,768 tokens: edited-BF16 14 of 31 continued (ended on their own 0, correct 0); edited-Q8_0 23 of 43 continued (ended on their own 1, correct 0).
