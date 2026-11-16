# weight-edit-vs-quantization

Read `README.md` first: it holds the question, the plan, the prior work and the rules.

- Owner: Philip. Purpose: a short, honest, reproducible measurement of one published result.
- Keep it simple: one question, one table, one demo. Optional extras only after the core run is done.
- `PREDICTION.md` must be filled in by Philip and committed before the first test run. Do not write it for him and do not edit it after.
- Machine: Apple M5, 16 GB. System Python is 3.14 with no ML libraries; create a project environment with `uv` (pick a Python version the ML libraries support).
- Qwen3.5-0.8B is listed on Hugging Face as an image-text-to-text model; only the text path is used here.
- Known trap: llama.cpp's default sampler reportedly changes the scores a lot. Fix sampler settings explicitly and record them.
- Explain results to Philip in plain words; he is learning quantization through this project.
