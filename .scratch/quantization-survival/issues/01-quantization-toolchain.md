# Which tool runs this model at full, 8-bit and 4-bit on this laptop?

Type: research
Status: resolved
Blocked by: none
Map: [does the edit survive quantization?](../map.md)

## Question

Which toolchain can run Qwen3.5-0.8B (text path only) at full precision, 8-bit and 4-bit on an Apple M5 with 16 GB, in one runtime, with every sampler setting fixed explicitly and a fixed seed, fully offline?

Compare at least llama.cpp (GGUF: F16, Q8_0, Q4_K_M), MLX (mlx-lm) and Hugging Face transformers. For each: does it support the Qwen3.5 architecture today; how are the 8-bit and 4-bit files produced from the published safetensors; what do its "8-bit" and "4-bit" actually mean (bits per weight, which tensors are left at higher precision); how are temperature, top-p, top-k, presence penalty, repetition penalty, seed, thinking on/off and the token limit set; what are its default sampler settings and how do they differ from MIT's (temperature 0.6, top-p 0.95, top-k 20, presence penalty 1.5).

Deliver a recommendation and the exact commands, plus what would have to be true for the full-precision row to be comparable to the 8-bit and 4-bit rows.

## Answer

Resolved 2026-11-12. Full findings: branch `research/quantization-toolchain` (commit `c192673`), file `research/quantization-toolchain.md`. Nothing was installed or run; commands are assembled from docs and source and still need a first real run.

**Recommendation: llama.cpp v0.9.0 (GGUF) for all six versions**, served by `llama-server` with every sampler setting passed explicitly. Full precision = `BF16`, 8-bit = `Q8_0`, 4-bit = `Q4_K_M`. It is the only candidate with first-party evidence of converting this exact checkpoint (text-only GGUF from the image-text model), and its sampler order is a flag. Second choice: mlx-lm 0.32.2 (uniform 4-bit, but sampler order is hard-coded and differs from MIT's). transformers is not recommended for the quantized rows and has no presence penalty.

Facts later tickets depend on:

- llama.cpp defaults differ from MIT's: temperature 0.8, top-k 40, min-p 0.05, presence penalty 0, temperature applied last, penalty window 64 tokens. Must set `--samplers "penalties;temperature;top_k;top_p"` and `--repeat-last-n` to the whole context.
- Thinking is on by default in llama.cpp but off by default from the chat template alone. Set it explicitly both ways.
- `Q8_0` is uniform (about 8.5 bits per weight). `Q4_K_M` is a mixed recipe: by the source rule the two edited tensors (`down_proj` of layers 15 and 19) get the lowest tier, `Q4_K`, while some other tensors get `Q6_K`. Inferred from source; confirm with `grep -E "blk\.(15|19)\.ffn_down"` on the quantize log.
- Token-limit signal: `finish_reason` is `"length"` at the limit, `"stop"` at a natural end.
- Not confirmed: BF16 speed on the Apple GPU (fallback `--outtype f16`); Homebrew binary names; that a fixed seed gives identical reruns.
- Run-time risk: rough estimate 35 to 105 hours for 200 questions across all rows at a 32,768 limit. Decided in [Lock the protocol](08-lock-the-protocol.md).
