# Which tool runs this model at full, 8-bit and 4-bit on this laptop?

Research for ticket `01-quantization-toolchain`. Date: 2026-11-12.
Method: documentation and source reading only. No model weights were downloaded, no model was run, nothing was installed. Only small text files were fetched (configs, model cards, chat template, tensor index, a conversion log, source files at release tags).

Labels used below: **[observed]** = read directly in the cited source; **[inferred]** = my reasoning from observed facts; **[not confirmed]** = could not be checked without running something.

---

## 1. Recommendation

**Use llama.cpp v0.9.0 (GGUF) for all six versions: `BF16` as full precision, `Q8_0` as 8-bit, `Q4_K_M` as 4-bit, served by `llama-server` with every sampler setting passed explicitly.**

Why this one:

- It is the only candidate where support for *this exact model revision* is shown by a first-party artefact: the llama.cpp organisation's own conversion log for `Qwen/Qwen3.5-0.8B` @ `2fc0636…` [observed, S7].
- The sampler chain (which filters run, and in which order) is a single flag, so it can be made to match the order MIT's runtime used. In mlx-lm the order is hard-coded and differs [observed, S10].
- `BF16` stores the published bfloat16 weights without any rounding, so the full-precision row uses the same numbers as the published safetensors [observed S4, S7; inferred lossless].
- The edited tensors (`down_proj` of layers 15 and 19) land in the *lowest* tier of `Q4_K_M` (plain `Q4_K`), so the 4-bit test is not softened for the edit [inferred from S5, see section 3].
- The server reports "stopped at token limit" as a distinct value (`finish_reason: "length"`, `stop_type: "limit"`) [observed, S6].

MLX (mlx-lm 0.32.2) is a sound second choice and has the cleaner definition of "4-bit" (uniform). Hugging Face transformers is not recommended for the quantized rows.

### 1.1 One-time setup

```sh
# Runtime + quantizer (Homebrew bottle is 0.9.0 today)
brew install llama.cpp
llama-server --version          # record this line in results/

# Converter script lives only in the source tree; pin the same tag
git clone --depth 1 --branch v0.9.0 https://github.com/ggml-org/llama.cpp vendor/llama.cpp

# Separate small Python env just for conversion (system Python 3.14 is too new for the pinned torch)
uv venv --python 3.12 .venv-convert
uv pip install --python .venv-convert/bin/python \
  -r vendor/llama.cpp/requirements/requirements-convert_hf_to_gguf.txt
# If the tokenizer fails to load, upstream says this is safe:
#   uv pip install --python .venv-convert/bin/python -U transformers
```

Binary names: the tools' own READMEs use `llama-server` / `llama-quantize`; the top-level README also shows a unified `llama serve` / `llama cli` form [observed, S6]. Which names the Homebrew bottle installs was **not confirmed**; check with `ls $(brew --prefix)/bin | grep llama`.

### 1.2 Build the six versions (run once per model: `base`, `edited`)

`$SRC` = local folder with the published safetensors (`models/base` or `models/edited`), `$NAME` = `base` or `edited`.

```sh
# Full precision: lossless bfloat16 -> BF16 GGUF. Text path only (vision tensors are skipped automatically).
.venv-convert/bin/python vendor/llama.cpp/convert_hf_to_gguf.py "$SRC" \
  --outtype bf16 --no-mtp \
  --outfile models/gguf/$NAME-BF16.gguf 2>&1 | tee results/convert-$NAME.log

# 8-bit and 4-bit, both made from the BF16 file (never from each other)
llama-quantize models/gguf/$NAME-BF16.gguf models/gguf/$NAME-Q8_0.gguf   Q8_0   2>&1 | tee results/quantize-$NAME-Q8_0.log
llama-quantize models/gguf/$NAME-BF16.gguf models/gguf/$NAME-Q4_K_M.gguf Q4_K_M 2>&1 | tee results/quantize-$NAME-Q4_K_M.log

# Evidence that the edited tensors got the type we think they got
grep -E "blk\.(15|19)\.ffn_down" results/quantize-$NAME-*.log
shasum -a 256 models/gguf/$NAME-*.gguf >> results/hashes.txt
```

`--no-mtp` leaves out the unused multi-token-prediction head (one extra block, used only for speculative decoding, which is off by default) [observed, S4, S6]. Using it or not must be the same for all six versions.

### 1.3 Run one version with every setting fixed

```sh
llama-server -m models/gguf/$NAME-$LEVEL.gguf \
  --offline --host 127.0.0.1 --port 8080 \
  -ngl all -c 34816 -np 1 -n 32768 --no-context-shift \
  --jinja --reasoning on --reasoning-format none --reasoning-budget -1 \
  --samplers "penalties;temperature;top_k;top_p" \
  --temp 0.6 --top-k 20 --top-p 0.95 --min-p 0 \
  --presence-penalty 1.5 --frequency-penalty 0 --repeat-penalty 1.0 --repeat-last-n 34816 \
  --seed 0
```

Checks that generate nothing (allowed before the prediction is committed):

```sh
curl -s http://127.0.0.1:8080/props > results/props-$NAME-$LEVEL.json      # server's effective default settings
curl -s http://127.0.0.1:8080/apply-template -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"TEST"}]}'                      # prompt must end with: <|im_start|>assistant\n<think>\n
```

Per question (this one generates; only after `PREDICTION.md` is committed). Settings are repeated in the request so the request file itself is the record:

```sh
curl -s http://127.0.0.1:8080/v1/chat/completions -H 'Content-Type: application/json' -d '{
  "messages": [{"role": "user", "content": "<question text>"}],
  "max_tokens": 32768,
  "temperature": 0.6, "top_p": 0.95, "top_k": 20, "min_p": 0,
  "presence_penalty": 1.5, "frequency_penalty": 0, "repeat_penalty": 1.0, "repeat_last_n": 34816,
  "samplers": ["penalties", "temperature", "top_k", "top_p"],
  "seed": 0, "cache_prompt": false, "stream": false,
  "chat_template_kwargs": {"enable_thinking": true},
  "reasoning_format": "none"
}'
```

Read from the response: `choices[0].finish_reason` (`"length"` = hit the token limit, `"stop"` = natural end), `usage.completion_tokens`, `timings.predicted_per_second`.

Baselines on the base model: thinking off = `--reasoning off` and `"chat_template_kwargs": {"enable_thinking": false}`; repetition penalty = change `--repeat-penalty` / `"repeat_penalty"` only.

### 1.4 Why each flag is there

| Flag | Reason | Source |
|---|---|---|
| `--samplers "penalties;temperature;top_k;top_p"` | Default chain is `penalties, dry, top_n_sigma, top_k, typ_p, top_p, min_p, xtc, temperature` (temperature **last**). Naming the chain removes every filter not listed and puts temperature before top-k/top-p. Penalties only run if `penalties` is in the list. | S6 `common/common.h`, `common/sampling.cpp` |
| `--min-p 0` | Default is `0.05`; MIT used none. Redundant once `min_p` is out of the chain, kept for the record. | S6 `common/common.h` |
| `--temp 0.6 --top-k 20` | Defaults are `0.80` and `40`. `--top-p 0.95` equals the default. | S6 |
| `--presence-penalty 1.5` | Default `0.0`. | S6 |
| `--repeat-last-n 34816` | Penalties only look at the last N tokens; default N is **64**. MIT's runtime penalises over the whole output, so N must cover the whole context. Negative values are rejected by this flag in v0.9.0. | S6 `common/arg.cpp`, `src/llama-sampler.cpp` |
| `--reasoning on` | Sets template variable `enable_thinking=true`. Default is `auto`, which in llama.cpp resolves to **on** when the template supports it. | S6 `common/arg.cpp`, `tools/server/server-context.cpp` |
| `--reasoning-format none` | Returns raw text (thinking and answer in one string) so the scorer sees exactly what was generated. | S6 server README |
| `--reasoning-budget -1` | No separate cap on thinking tokens (this is the default; stated for the record). | S6 |
| `-n 32768`, `-c 34816`, `-np 1` | Token limit, context = limit + 2048 for the prompt (same as MIT's `max_model_len=34816`), one slot so the whole context belongs to one request. | S2, S6 |
| `--no-context-shift` | Default is already disabled; with it off, running out of context ends the answer with stop type `limit` instead of silently dropping old tokens. | S6 |
| `"cache_prompt": false` | Upstream warns cached prompts can change results slightly. | S6 server README |
| `--offline` | "forces use of cache, prevents network access". Also turn Wi-Fi off. | S6 `common/arg.cpp` |

---

## 2. What the model is, and the image-text-to-text question

Observed in `config.json` of both repos (byte-identical configs) [S1, S2]:

- `"architectures": ["Qwen3_5ForConditionalGeneration"]`, `"model_type": "qwen3_5"`, text part `"model_type": "qwen3_5_text"`, 24 layers, of which 18 are `linear_attention` (a gated delta-net, not ordinary attention) and 6 are `full_attention`.
- `"dtype": "bfloat16"`, `"tie_word_embeddings": true`, a `vision_config` block, and `"mtp_num_hidden_layers": 1`.
- Tensor index: 488 tensors = language model + `model.visual.*` (vision tower) + `mtp.*` (multi-token-prediction head).
- Edited tensors as named by the edited model's card: `model.language_model.layers.15.mlp.down_proj.weight` and `…layers.19.mlp.down_proj.weight`; "64 output columns of `down_proj` in each layer (131,072 weights)". Shape is 1024 x 3584, and 2 x 64 x 1024 = 131,072 [observed S2; arithmetic mine].
- No `generation_config.json` in either repo ("Entry not found"), so no tool inherits sampler defaults from the model [observed].
- Both repos ship the same `chat_template.jinja` (compared byte for byte) [observed].

**Does the image-text-to-text listing break text-only conversion? No, for all three tools.**

- llama.cpp: the converter registers `"Qwen3_5ForConditionalGeneration", "Qwen3_5ForCausalLM", "Qwen3_5TextModel"` on one text class, and the base text converter drops every tensor whose name contains `visual.`, `vision.`, `patch_embed`, `merger.` etc. ("Skip multimodal tensors") [observed, S4]. The official conversion log shows the full multimodal checkpoint going in and a 335-tensor text GGUF coming out, with no `--mmproj` step [observed, S7].
- mlx-lm: `sanitize()` skips keys starting with `vision_tower` or `model.visual`, and removes `mtp.` keys [observed, S9].
- transformers: docs say "Use `Qwen3_5ForCausalLM` for text-only generation" [observed, S12].
- The edited model's card states the same thing from the other side: "the post evaluated a text-only export of the model, and this checkpoint is the full multimodal release. The language-model tensors are identical (hash-verified), and text prompts do not use the vision tower." [observed, S2]

---

## 3. Comparison

### 3.1 Architecture support today

| Tool | Release checked | Evidence | Verdict |
|---|---|---|---|
| llama.cpp | v0.9.0, 2026-11-04 | Converter: `@ModelBase.register("Qwen3_5ForConditionalGeneration", …)` with `model_arch = gguf.MODEL_ARCH.QWEN35`; runtime file `src/models/qwen35.cpp`; Metal kernel `gated_delta_net.metal`; top-level README uses `ggml-org/Qwen3.5-0.8B-GGUF` as its example; official conversion log for this revision. | Supported, with direct evidence for this model |
| mlx-lm | v0.32.2, 2026-10-16 | `mlx_lm/models/qwen3_5.py` exists (file name = `model_type`), with `GatedDeltaNet` and vision/MTP stripping. | Supported in source. **Not confirmed** on this exact checkpoint (no first-party conversion log found) |
| transformers | v5.22.2, 2026-11-06 | `src/transformers/models/qwen3_5/` with `Qwen3_5ForCausalLM`, `Qwen3_5ForConditionalGeneration`. | Supported |

### 3.2 How the files are made, and what "8-bit" and "4-bit" mean

**llama.cpp / GGUF** [observed S4, S5, S7 unless marked]

- Path: safetensors -> `convert_hf_to_gguf.py --outtype bf16` -> `llama-quantize … Q8_0 | Q4_K_M`.
- Never quantized at any level (kept as 32-bit floats): 1-D tensors, anything ending `_norm.weight`, and `ssm_conv1d` (the small convolution in the linear-attention layers). Quote: "quantize only 2D+ tensors", "do not quantize norm tensors", "do not quantize Mamba/Kimi's small conv1d weights".
- `BF16`: all 2-D tensors stored as bfloat16, i.e. the published values unchanged. Log: `blk.15.ffn_down.weight, torch.bfloat16 --> BF16`, model size `16.01 BPW`.
- `Q8_0`: **uniform**. Every quantizable tensor becomes `q8_0`. Log for this model: `blk.15.ffn_down.weight … converting to q8_0`, `blk.19.ffn_down.weight … converting to q8_0`, `token_embd.weight … converting to q8_0`; total `8.52 BPW`. (The extra half bit is the per-block scale.)
- `Q4_K_M`: **not uniform**. It is a recipe that gives some tensors more bits. From `llama_tensor_get_type_impl`:
  - `use_more_bits(i, n) = i < n/8 || i >= 7*n/8 || (i - n/8) % 3 == 2`
  - `ffn_down` (this is `mlp.down_proj`): `Q6_K` if `use_more_bits`, otherwise `Q4_K`.
  - `attn_v`: `Q6_K` if `use_more_bits` (counted over attention-V tensors), otherwise `Q4_K`.
  - `attn_qkv`: `Q5_K`.
  - Token embeddings when tied to the output layer (the case here): `Q6_K`.
  - Everything else: `Q4_K`.
- **[inferred]** For 24 layers (or 25 with the MTP block; same result), `use_more_bits` is true for layers 0, 1, 2, 5, 8, 11, 14, 17, 20, 21, 22, 23. **Layers 15 and 19 are not in that list, so both edited tensors are stored as `Q4_K`**, the lowest tier in the file, while half of the other `down_proj` tensors get `Q6_K`. This is derived from source, not from a log (the official repo ships `Q4_0`, not `Q4_K_M`). The `grep` in section 1.2 confirms it at build time without running the model.
- **[inferred]** Consequence for the write-up: "4-bit" should be reported as "`Q4_K_M`, about 4.9 bits per weight on average, edited tensors at `Q4_K` (about 4.5)". The 4.89 average is upstream's figure for a different model (Llama-3.1-8B) [observed S5 quantize README]; the true figure for this model will be printed by `llama-quantize`. It will be higher here because the embedding table is about a third of the weights and gets `Q6_K` [inferred].
- A uniform 4-bit alternative exists: `llama-quantize --pure … Q4_K_M` ("disable k-quant mixtures and quantizes all tensors to the same type") or `Q4_0` [observed S5].

**mlx-lm** [observed S9, S10]

- Path: `mlx_lm.convert --hf-path $SRC --mlx-path out --dtype bfloat16` (full), add `-q --q-bits 8` or `-q --q-bits 4` (default mode `affine`, default group size 64).
- **Uniform**: for this non-MoE model `quant_predicate` returns `None`, so every layer that can be quantized (linear layers and the embedding table) gets the same bit width, including both edited tensors. Layers without a quantized form (convolution, norms) stay in floating point. Mixed recipes exist (`--quant-predicate mixed_4_6`, modelled on Q4_K_M) but are opt-in.
- Each group of 64 weights stores a scale and an offset, so real cost is about 4.5 and 8.5 bits per weight [inferred from group size and 16-bit scale/bias]; the tool prints the measured value ("Quantized model with N bits per weight").

**transformers** [observed S12, S13]

- Full precision: load safetensors directly in bfloat16. Nothing to convert.
- 8-bit / 4-bit: via bitsandbytes at load time. **One-line check on the Apple Silicon belief: it is out of date.** bitsandbytes 0.50.2 publishes a `macosx_14_0_arm64` wheel, and its README lists "macOS 14+ / arm64 / CPU and Metal `mps`" with LLM.int8 "supported*" and 4-bit "supported", footnoted "may lack in performance optimizations". The transformers 5.22.2 docs still describe the backends without macOS and mark Metal as partial. **Not confirmed** that it works with this architecture on MPS.
- Which tensors bitsandbytes leaves at higher precision was not checked here.

### 3.3 Sampler settings: how they are set, and the defaults

MIT's settings [observed S2, both the card and `eval/scores_*.json`]: vLLM, thinking on, `temperature 0.6, top_p 0.95, top_k 20, presence_penalty 1.5, max_tokens 32768, seed 0`.

| Setting | MIT | llama.cpp default -> how to set | mlx-lm default -> how to set | transformers default -> how to set |
|---|---|---|---|---|
| temperature | 0.6 | 0.80 -> `--temp` | 0.0 (greedy) -> `make_sampler(temp=)` | from `GenerationConfig` -> `temperature=` |
| top-p | 0.95 | 0.95 -> `--top-p` | 1.0 (off) -> `top_p=` | `top_p=` |
| top-k | 20 | 40 -> `--top-k` | 0 (off) -> `top_k=` | `top_k=` |
| min-p | none | **0.05** -> `--min-p 0` | 0.0 | n/a |
| presence penalty | 1.5 | 0.0 -> `--presence-penalty` | none -> `make_logits_processors(presence_penalty=)` (no flag on `mlx_lm.generate`; available in Python and in `mlx_lm.server`) | **does not exist** in `GenerationConfig`; needs a custom logits processor |
| penalty window | whole output [not confirmed for vLLM] | last **64** tokens -> `--repeat-last-n` | last **20** tokens -> `presence_context_size=` | n/a |
| repetition penalty | 1.0 | 1.00 -> `--repeat-penalty` | none -> `repetition_penalty=` | `repetition_penalty=` |
| order of filters | temperature, then top-k / top-p [not confirmed for vLLM] | penalties, …, top_k, top_p, min_p, …, **temperature last** -> `--samplers` | **fixed**: top_p, min_p, xtc, top_k, then temperature at the draw; change only by writing a custom sampler function | temperature, top-k, top-p |
| seed | 0 | random -> `--seed` / `"seed"` | none -> `mx.random.seed()` / `--seed` | `torch.manual_seed()` |
| token limit | 32,768 | unlimited (-1) -> `-n` / `"max_tokens"` | 100 -> `max_tokens=` | `max_new_tokens=` |

### 3.4 Thinking on / off

The chat template ends with [observed S1]:

```
{%- if enable_thinking is defined and enable_thinking is true %}
    {{- '<think>\n' }}
{%- else %}
    {{- '<think>\n\n</think>\n\n' }}
```

So with no flag the template turns thinking **off**; Qwen's card agrees: "Qwen3.5-0.8B operates in non-thinking mode by default" [observed S1].

| Tool | Unset behaviour | How to set |
|---|---|---|
| llama.cpp | **On.** `--reasoning` defaults to `auto`; server code: `enable_thinking = params_base.enable_reasoning != 0 && template_supports_thinking`. Opposite of the other two tools. | `--reasoning on|off`; per request `"chat_template_kwargs": {"enable_thinking": true}`. Passing it via `--chat-template-kwargs` is deprecated. |
| mlx-lm | Off (template default) [inferred] | `--chat-template-config '{"enable_thinking": true}'` or `tokenizer.apply_chat_template(..., enable_thinking=True)` |
| transformers | Off (template default) | `tokenizer.apply_chat_template(..., enable_thinking=True)` (as in the edited model's card) |

### 3.5 How "stopped at the token limit" is reported

| Tool | Signal | Source |
|---|---|---|
| llama.cpp server | Chat endpoint: `finish_reason` is `"length"` unless the stop was an end token or stop word (`"stop"`). Native endpoint: `stop_type` = `eos` / `limit` / `word`, plus `truncated`. Running out of context (not just `-n`) also gives `limit`. | S6 `tools/server/server-task.cpp`, `server-context.cpp`, README |
| mlx-lm | `GenerationResponse.finish_reason`: `"stop" if token in tokenizer.eos_token_ids else "length"`. Also gives `generation_tps` and `peak_memory`. | S10 `mlx_lm/generate.py` |
| transformers | No field. Must be derived: output length equals `max_new_tokens` and last token is not an end token. | S12 |

All three also report tokens per second; llama.cpp (`timings.predicted_per_second`) and mlx-lm (`generation_tps`, `peak_memory`) do it without extra code.

### 3.6 Summary

| | llama.cpp | mlx-lm | transformers |
|---|---|---|---|
| All three precision levels in one runtime | yes | yes | yes on paper; quantized rows unproven on Mac |
| Proof it handles this exact model | first-party log | source only | source only |
| 8-bit uniform | yes | yes | not checked |
| 4-bit uniform | no by default (edited tensors at lowest tier); `--pure` available | yes | not checked |
| Sampler order controllable | yes, one flag | only with custom code | fixed, matches MIT |
| Presence penalty | yes | yes (Python/server) | no |
| Token-limit signal | explicit | explicit | derive by hand |
| Format people actually ship | yes (GGUF) | Apple only | n/a |

Not examined: Ollama (installed, but it adds its own defaults layer on top of a GGUF, which works against "every setting explicit"); vLLM (MIT's runtime; not targeted at Apple Silicon as far as I know, **not confirmed**).

---

## 4. What must be true for the full-precision row to be comparable to the 8-bit and 4-bit rows

1. **Same runtime and same binary** for all six versions (record `llama-server --version`). The full-precision row is then the BF16 GGUF, not PyTorch. Any difference between rows is then the stored precision, not the software.
2. **Full precision is really lossless.** Use `--outtype bf16`, not `f16`: the source is bfloat16, and converting to float16 can round very small weights [inferred]. Check the convert log shows `torch.bfloat16 --> BF16` for `blk.15.ffn_down.weight` and `blk.19.ffn_down.weight`.
3. **8-bit and 4-bit are both made from the BF16 file**, with the same `llama-quantize` build, no importance matrix, same options for base and edited.
4. **Same converter options for base and edited** (`--no-mtp` on both or neither), so the tensor list and the Q4_K_M layer pattern are identical.
5. **Identical launch flags and request body** for every version; only `-m` changes. Save `/props` per version.
6. **Same prompt text**: same question wording, same system prompt (none), thinking flag explicit. Confirm with `/apply-template`.
7. **Same seed**, with the understanding that a seed does not make different precision levels produce the same text; it only makes one version repeatable (and even that is "mostly", see risk 5).
8. **Same token limit and context size**, so "reached the limit" means the same thing in every row.

Comparability with MIT's published numbers is a separate, weaker claim: different runtime (vLLM on an H200), and two details of their sampler I could not confirm (section 5, risk 3).

---

## 5. Open risks and things not confirmed

1. **Nothing here was run.** Every command is assembled from docs and source at the tags listed. Flag spellings are quoted from source, but end-to-end behaviour on this Mac is unconfirmed.
2. **Run time may not fit the deadline.** MIT's own files show mean generated tokens per answer of 31,690 (base) and 21,704 (edited) [observed S2]. With 200 questions, three base rows, three edited rows and one penalty baseline, that is on the order of 38 million tokens [inferred]. At an assumed 100 to 300 tokens per second, one stream, that is roughly 35 to 105 hours. Tokens per second on the M5 is unknown. The question count, the token limit, or parallel slots (`-np`) must be decided with this in mind; parallel slots change how context is shared between requests and were not researched in depth.
3. **Presence-penalty details vs vLLM not confirmed.** In llama.cpp the server feeds the prompt tokens into the penalty history too (`init_sampler` accepts every prompt token) [observed S6], and the window is a token count. Whether vLLM penalises prompt tokens, and its exact filter order, were not checked. Internal comparison across the six versions is unaffected; closeness to MIT's absolute numbers may be.
4. **BF16 on the Apple GPU.** The Metal backend has BF16 support paths, but at least one operation check returns "not supported" when an input is BF16 [observed S6 `ggml-metal-device.m`]. Some work may fall back to the CPU, making the full-precision rows slower than the quantized ones. Correctness should be unaffected [inferred]; speed is **not confirmed**. Fallback if too slow: `--outtype f16` for both models, and say so in the write-up (no longer strictly lossless).
5. **Repeatability.** Upstream notes logits are "not guaranteed to be bit-for-bit identical for different batch sizes" [observed S6]. Treat the seed as "fixed and recorded", not as a guarantee of identical reruns.
6. **Q4_K_M tier for layers 15 and 19 is inferred**, not seen in a log. Confirm with the `grep` in 1.2 before any generation. If it shows `q6_k` for either, the 4-bit row is softer than described and `--pure` should be considered.
7. **"4-bit" is a label, not a number.** Report measured bits per weight from the quantize log next to each row.
8. **Converter environment.** The pinned requirements install transformers 4 and torch 2.11.0; upstream says newer models may need `pip install -U transformers` [observed S5]. Whether this model needs it is not confirmed.
9. **Homebrew bottle contents** (binary names, Metal enabled) not confirmed; `docs/build.md` says Metal is on by default on macOS when building from source.
10. **llama.cpp default for thinking is the opposite of the other tools** (on vs off). The thinking-off baseline must set it explicitly, and the `/apply-template` check should be saved for both modes.
11. **mlx-lm on this exact checkpoint** is unproven; relevant only if the recommendation is changed.
12. **Known model behaviour, from Qwen themselves**: "Qwen3.5-0.8B is more prone to entering thinking loops compared to other Qwen3.5 models, which may prevent it from terminating generation properly" [observed S1]. This is the looping the edit targets; it also supports the criticism that thinking-off recovers much of the gain, which the thinking-off baseline will measure.

---

## 6. Sources

All fetched 2026-11-12. Source files were read at the release tag named.

- **S1** Base model: https://huggingface.co/Qwen/Qwen3.5-0.8B (revision `2fc06364715b967f1860aea9cf38778875588b17`): `config.json`, `chat_template.jinja`, `model.safetensors.index.json`, `README.md`; file list via https://huggingface.co/api/models/Qwen/Qwen3.5-0.8B
- **S2** Edited model: https://huggingface.co/RikiyaT/Qwen3.5-0.8B-weight-space-programming (revision `d1671a178705bcab7644806d23c535517f35723b`): `README.md`, `config.json`, `chat_template.jinja`, `eval/scores_base_math500.json`, `eval/scores_edited_math500.json`
- **S3** llama.cpp release v0.9.0 (2026-11-04): https://github.com/ggml-org/llama.cpp/releases/tag/v0.9.0 ; Homebrew formula version 0.9.0: https://formulae.brew.sh/api/formula/llama.cpp.json
- **S4** llama.cpp converter @ v0.9.0: `convert_hf_to_gguf.py`, `conversion/qwen.py` (class `Qwen3_5TextModel`, `_QwenMtpMixin`), `conversion/base.py` (`TextModel.filter_tensors`, `_tensor_requires_f32`, dtype heuristics), `requirements/requirements-convert_hf_to_gguf.txt` — https://github.com/ggml-org/llama.cpp/tree/v0.9.0
- **S5** llama.cpp quantizer @ v0.9.0: `src/llama-quant.cpp` (`tensor_allows_quantization`, `llama_tensor_get_type_impl`), `tools/quantize/README.md`
- **S6** llama.cpp runtime @ v0.9.0: `common/common.h` (`common_params_sampling` defaults), `common/arg.cpp` (flags), `common/sampling.cpp` (chain construction, sampler names), `src/llama-sampler.cpp` (penalties), `tools/server/README.md`, `tools/server/server-task.cpp` (`finish_reason`, `stop_type`), `tools/server/server-context.cpp` (limit checks, `init_sampler`, thinking default), `tools/server/server-common.cpp`, `common/chat.cpp`, `ggml/src/ggml-metal/ggml-metal-device.m`, `README.md`, `docs/install.md`, `docs/build.md`
- **S7** Official GGUF conversion of the base model: https://huggingface.co/ggml-org/Qwen3.5-0.8B-GGUF — `convert.log`, `.src_sha` (`PRIMARY=2fc06364715b967f1860aea9cf38778875588b17`), `README.md`, file list (`BF16`, `Q8_0`, `Q4_0`)
- **S8** mlx-lm release v0.32.2 (2026-10-16): https://github.com/ml-explore/mlx-lm/releases/tag/v0.32.2 ; PyPI `mlx-lm 0.32.2` (requires Python >= 3.11), `mlx 0.32.4`
- **S9** mlx-lm @ v0.32.2: `mlx_lm/models/qwen3_5.py`, `mlx_lm/convert.py`, `mlx_lm/utils.py` (`quantize_model`) — https://github.com/ml-explore/mlx-lm/tree/v0.32.2
- **S10** mlx-lm @ v0.32.2: `mlx_lm/sample_utils.py`, `mlx_lm/generate.py`, `mlx_lm/server.py`
- **S11** transformers release v5.22.2 (2026-11-06): https://github.com/huggingface/transformers/releases/tag/v5.22.2
- **S12** transformers @ v5.22.2: `src/transformers/models/qwen3_5/modeling_qwen3_5.py`, `docs/source/en/model_doc/qwen3_5.md`, `src/transformers/generation/configuration_utils.py`, `docs/source/en/quantization/overview.md`, `docs/source/en/quantization/bitsandbytes.md`
- **S13** bitsandbytes: `README.md` on `main` (accelerator support table) https://github.com/bitsandbytes-foundation/bitsandbytes ; PyPI `bitsandbytes 0.50.2` wheel list https://pypi.org/pypi/bitsandbytes/json
