# What rounding does to the edit

Produced by `src/edit_rounding.py` from the GGUF files in `models/gguf/`. No model was run.
Added after the run (post-hoc), to test the reason in `PREDICTION.md` ("rounding erases the edit itself").

Terms: *true edit* = edited minus base at 16-bit. *Stored edit* = edited minus base, both read from the
quantized files. *Rounding error* = quantized weights minus 16-bit weights. Sizes are norms (root of the sum of squares).

## `blk.15.ffn_down.weight`

- Edit size relative to the tensor: 10.64%. Columns touched: 64 of 3584.
- Blocks of 32 weights per row that contain an edited column: 35 of 112.

| Level | Stored as | Stored edit vs true edit: direction (cosine) | Stored edit vs true edit: size | Rounding error on edited tensor, relative to the edit | Rounding error, whole tensor: base / edited | Rounding error, untouched columns in blocks with an edit: base / edited |
|---|---|---|---|---|---|---|
| Q8_0 | Q8_0 | 0.9998 | 1.000 | 5.41% | 0.57% / 0.57% | 0.58% / 0.60% |
| Q4_K_M | Q4_K | 0.9328 | 1.069 | 70.37% | 7.44% / 7.46% | 7.55% / 7.72% |

## `blk.19.ffn_down.weight`

- Edit size relative to the tensor: 8.11%. Columns touched: 64 of 3584.
- Blocks of 32 weights per row that contain an edited column: 37 of 112.

| Level | Stored as | Stored edit vs true edit: direction (cosine) | Stored edit vs true edit: size | Rounding error on edited tensor, relative to the edit | Rounding error, whole tensor: base / edited | Rounding error, untouched columns in blocks with an edit: base / edited |
|---|---|---|---|---|---|---|
| Q8_0 | Q8_0 | 0.9998 | 1.000 | 6.78% | 0.55% / 0.55% | 0.56% / 0.57% |
| Q4_K_M | Q4_K | 0.8954 | 1.110 | 89.60% | 7.23% / 7.25% | 7.34% / 7.43% |

Reading the table:

- A cosine near 1 and a size near 1 mean the edit came through rounding intact.
- The last column checks a side effect: each block shares one scale, so a large edited weight can make the
  rounding of its untouched neighbours coarser. If edited > base there, the edit costs precision elsewhere.
- This measures the weights only. It does not show why the edited model's accuracy drops.
