# Results

Questions: 100 from MATH-500 (id lists in `data/question_ids.json`). One response per question.
Looping = the response hit the token limit. Intervals are Wilson 95%.
Produced by `python -m wevq.table`; per-response flags are in `results/flags/`.

| Version | Questions | Looping | Looping without an answer | Accuracy | Mean tokens |
|---|---|---|---|---|---|
| base, full precision (16-bit) | 100 | 88.0% (80-93) | 75.0% (66-82) | 14.0% (9-22) | 29,439 |
| edited, full precision (16-bit) | 100 | 31.0% (23-41) | 29.0% (21-39) | 61.0% (51-70) | 20,877 |
| base, 8-bit | 100 | 85.0% (77-91) | 76.0% (67-83) | 15.0% (9-23) | 28,625 |
| edited, 8-bit | 100 | 43.0% (34-53) | 39.0% (30-49) | 45.0% (36-55) | 22,636 |
| base, 4-bit (Q4_K_M) | 100 | 84.0% (76-90) | 77.0% (68-84) | 16.0% (10-24) | 28,173 |
| edited, 4-bit (Q4_K_M) | 100 | 29.0% (21-39) | 26.0% (18-35) | 42.0% (33-52) | 19,428 |
| base, thinking off | 100 | 27.0% (19-36) | 19.0% (13-28) | 49.0% (39-59) | 11,730 |
| base, repetition penalty 1.1 | 100 | 74.0% (65-82) | 67.0% (57-75) | 25.0% (18-34) | 26,360 |

## Reduction in looping, base vs edited at each precision level

| Precision level | Base looping | Edited looping | Reduction (points) | Only base loops / only edited loops | McNemar p | Survives ratio (95% interval) | Verdict |
|---|---|---|---|---|---|---|---|
| full precision (16-bit) | 88.0% | 31.0% | 57.0 | 57 / 0 | 1.4e-17 | reference | valid |
| 8-bit | 85.0% | 43.0% | 42.0 | 44 / 2 | 3.1e-11 | 0.74 (0.57-0.93) | survives |
| 4-bit (Q4_K_M) | 84.0% | 29.0% | 55.0 | 56 / 1 | 8e-16 | 0.96 (0.77-1.20) | survives |

Survives ratio = reduction at that level divided by the reduction at full precision; the interval is a paired bootstrap over questions (10,000 resamples). Verdict: survives if the ratio is at least 0.5; "cannot be called" if the interval contains 0.5.

## Settings

- `base-BF16`: `models/gguf/base-BF16.gguf` (1,516,744,736 bytes), thinking on, max 32,768 new tokens, 8 streams, llama.cpp build `b12110-cd959bae9`, sampling `{"temperature": 0.6, "top_k": 20, "top_p": 0.95, "min_p": 0.0, "presence_penalty": 1.5, "frequency_penalty": 0.0, "repeat_penalty": 1.0, "repeat_last_n": 34816, "samplers": ["penalties", "temperature", "top_k", "top_p"], "seed": 0}`
- `edited-BF16`: `models/gguf/edited-BF16.gguf` (1,516,744,672 bytes), thinking on, max 32,768 new tokens, 8 streams, llama.cpp build `b12110-cd959bae9`, sampling `{"temperature": 0.6, "top_k": 20, "top_p": 0.95, "min_p": 0.0, "presence_penalty": 1.5, "frequency_penalty": 0.0, "repeat_penalty": 1.0, "repeat_last_n": 34816, "samplers": ["penalties", "temperature", "top_k", "top_p"], "seed": 0}`
- `base-Q8_0`: `models/gguf/base-Q8_0.gguf` (811,843,616 bytes), thinking on, max 32,768 new tokens, 8 streams, llama.cpp build `b12110-cd959bae9`, sampling `{"temperature": 0.6, "top_k": 20, "top_p": 0.95, "min_p": 0.0, "presence_penalty": 1.5, "frequency_penalty": 0.0, "repeat_penalty": 1.0, "repeat_last_n": 34816, "samplers": ["penalties", "temperature", "top_k", "top_p"], "seed": 0}`
- `edited-Q8_0`: `models/gguf/edited-Q8_0.gguf` (811,843,552 bytes), thinking on, max 32,768 new tokens, 8 streams, llama.cpp build `b12110-cd959bae9`, sampling `{"temperature": 0.6, "top_k": 20, "top_p": 0.95, "min_p": 0.0, "presence_penalty": 1.5, "frequency_penalty": 0.0, "repeat_penalty": 1.0, "repeat_last_n": 34816, "samplers": ["penalties", "temperature", "top_k", "top_p"], "seed": 0}`
- `base-Q4_K_M`: `models/gguf/base-Q4_K_M.gguf` (529,297,440 bytes), thinking on, max 32,768 new tokens, 8 streams, llama.cpp build `b12110-cd959bae9`, sampling `{"temperature": 0.6, "top_k": 20, "top_p": 0.95, "min_p": 0.0, "presence_penalty": 1.5, "frequency_penalty": 0.0, "repeat_penalty": 1.0, "repeat_last_n": 34816, "samplers": ["penalties", "temperature", "top_k", "top_p"], "seed": 0}`
- `edited-Q4_K_M`: `models/gguf/edited-Q4_K_M.gguf` (529,297,376 bytes), thinking on, max 32,768 new tokens, 8 streams, llama.cpp build `b12110-cd959bae9`, sampling `{"temperature": 0.6, "top_k": 20, "top_p": 0.95, "min_p": 0.0, "presence_penalty": 1.5, "frequency_penalty": 0.0, "repeat_penalty": 1.0, "repeat_last_n": 34816, "samplers": ["penalties", "temperature", "top_k", "top_p"], "seed": 0}`
- `baseline-thinking-off`: `models/gguf/base-BF16.gguf` (1,516,744,736 bytes), thinking off, max 32,768 new tokens, 8 streams, llama.cpp build `b12110-cd959bae9`, sampling `{"temperature": 0.6, "top_k": 20, "top_p": 0.95, "min_p": 0.0, "presence_penalty": 1.5, "frequency_penalty": 0.0, "repeat_penalty": 1.0, "repeat_last_n": 34816, "samplers": ["penalties", "temperature", "top_k", "top_p"], "seed": 0}`
- `baseline-repeat-penalty`: `models/gguf/base-BF16.gguf` (1,516,744,736 bytes), thinking on, max 32,768 new tokens, 8 streams, llama.cpp build `b12110-cd959bae9`, sampling `{"temperature": 0.6, "top_k": 20, "top_p": 0.95, "min_p": 0.0, "presence_penalty": 1.5, "frequency_penalty": 0.0, "repeat_penalty": 1.1, "repeat_last_n": 34816, "samplers": ["penalties", "temperature", "top_k", "top_p"], "seed": 0}`
