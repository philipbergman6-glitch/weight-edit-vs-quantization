# Which tool runs this model at full, 8-bit and 4-bit on this laptop?

Type: research
Status: claimed
Blocked by: none
Map: [does the edit survive quantization?](../map.md)

## Question

Which toolchain can run Qwen3.5-0.8B (text path only) at full precision, 8-bit and 4-bit on an Apple M5 with 16 GB, in one runtime, with every sampler setting fixed explicitly and a fixed seed, fully offline?

Compare at least llama.cpp (GGUF: F16, Q8_0, Q4_K_M), MLX (mlx-lm) and Hugging Face transformers. For each: does it support the Qwen3.5 architecture today; how are the 8-bit and 4-bit files produced from the published safetensors; what do its "8-bit" and "4-bit" actually mean (bits per weight, which tensors are left at higher precision); how are temperature, top-p, top-k, presence penalty, repetition penalty, seed, thinking on/off and the token limit set; what are its default sampler settings and how do they differ from MIT's (temperature 0.6, top-p 0.95, top-k 20, presence penalty 1.5).

Deliver a recommendation and the exact commands, plus what would have to be true for the full-precision row to be comparable to the 8-bit and 4-bit rows.
