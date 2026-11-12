# Speed test, with file size and memory per version

Type: task
Status: resolved
Blocked by: 01, 04, 06
Map: [does the edit survive quantization?](../map.md)

## Question

Manual work (agent alone). Using the toolchain chosen in ticket 01, build what is needed and measure on this laptop, per precision level: file size on disk, memory used while running, and tokens per second. Use a neutral prompt, not benchmark questions, and do not report how often anything loops.

The answer records the numbers and a time budget: how long 200 questions take per version at token limits of 32,768, 16,384, 8,192 and 4,096 if every response ran to the limit.

## Answer

Resolved 2026-11-12. Numbers in `results/speed.md` (raw JSON in `results/speed/`), scripts `src/speed_test.py` and `src/speed_report.py`. Only a neutral prompt was generated, with end-of-text ignored; nothing about looping was observed or recorded.

- **Toolchain works as researched:** llama.cpp 0.9.0 from Homebrew (`llama-server`, `llama-quantize`), converter from the v0.9.0 source in `vendor/llama.cpp` with its own environment `.venv-convert`. The converter must be run without `-I`.
- **Six versions built** in `models/gguf/`: `{base,edited}-{BF16,Q8_0,Q4_K_M}.gguf`. Conversion used `--outtype bf16 --no-mtp`; logs in `results/convert-*.log` and `results/quantize-*.log`.
- **What the levels are:** BF16 16.01 bits per weight, 1,517 MB. Q8_0 8.52 bits per weight, 812 MB, uniform. Q4_K_M 5.51 bits per weight on average, 529 MB, mixed: 162 tensors at `q4_K`, 25 at `q6_K`.
- **Confirmed on the real files:** the two edited tensors (`blk.15.ffn_down.weight`, `blk.19.ffn_down.weight`) are stored as `q8_0` in the 8-bit file and as `q4_K` (the lower tier) in the 4-bit file.
- **Speed, one stream:** BF16 65 tokens/s, Q8_0 102, Q4_K_M 123. **Eight streams, total:** BF16 237, Q8_0 289, Q4_K_M 294. Four streams on Q8_0: 229.
- **Memory:** about 0.6 GB footprint per server with one 34,816-token stream, about 3.8 GB with eight, plus the memory-mapped model file. All fits in 16 GB.
- **Time budget, worst case, 200 questions, 8 rows, 8 streams:** 56 h at a 32,768 limit, 28 h at 16,384, 14 h at 8,192, 7 h at 4,096.
- Caveats: measured on battery; speed measured over the first 4,096 to 8,192 tokens only; BF16 is the slowest level (an F16 file might be faster but is not bit-identical to the published weights; not tested).
