# Speed, memory and file size per precision level

Produced by `src/speed_test.py` and `src/speed_report.py` on an Apple M5 (10 cores, 16 GB), llama.cpp 0.9.0,
all layers on the GPU, running on battery. Base model files; the edited files have the same size and layout.
Each run generated a fixed number of tokens from a neutral prompt with end-of-text ignored.
This measures speed only and says nothing about looping or accuracy.

| Precision level | File size | Bits per weight | Streams | Tokens generated | Tokens/s per stream | Tokens/s total | Memory footprint |
|---|---|---|---|---|---|---|---|
| BF16 | 1517 MB | 16.01 | 1 | 8,192 | 64.8 | 64.7 | 627 MB |
| BF16 | 1517 MB | 16.01 | 8 | 32,768 | 29.7 | 236.8 | 3,800 MB |
| Q8_0 | 812 MB | 8.52 | 1 | 8,192 | 102.0 | 102.0 | 626 MB |
| Q8_0 | 812 MB | 8.52 | 4 | 16,384 | 57.4 | 229.1 | 1,986 MB |
| Q8_0 | 812 MB | 8.52 | 8 | 32,768 | 36.1 | 288.9 | 3,802 MB |
| Q4_K_M | 529 MB | 5.51 | 1 | 8,192 | 123.3 | 122.8 | 626 MB |
| Q4_K_M | 529 MB | 5.51 | 8 | 32,768 | 36.9 | 294.2 | 3,800 MB |

Notes:

- Bits per weight are from the `llama-quantize` logs (`results/quantize-*.log`). The 4-bit file is a mixed recipe: 5.51 bits per weight on average.
- Memory footprint is the server process's `phys_footprint` after generation, with a 34,816-token context per stream. It does not include the model file itself, which is memory-mapped; add the file size for an upper bound on total memory.
- Speeds were measured over the first 4,096 to 8,192 tokens of a response. Longer responses may be slower per token.

## Time budget

Worst case: 200 questions per row, every response running to the token limit, 8 streams,
using the measured 8-stream totals above. Planned rows: base and edited at each precision level, plus two baselines at full precision (8 rows).

| Token limit | One BF16 row | One Q8_0 row | One Q4_K_M row | All 8 rows |
|---|---|---|---|---|
| 32,768 | 7.7 h | 6.3 h | 6.2 h | 56 h |
| 16,384 | 3.8 h | 3.2 h | 3.1 h | 28 h |
| 8,192 | 1.9 h | 1.6 h | 1.5 h | 14 h |
| 4,096 | 1.0 h | 0.8 h | 0.8 h | 7 h |

Real runs should be shorter: responses that finish early free their stream for the next question.
