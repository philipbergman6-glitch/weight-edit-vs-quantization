# Download both models, record hashes, diff the weights, confirm the edit

Type: task
Status: resolved
Blocked by: none
Map: [does the edit survive quantization?](../map.md)

## Question

Manual work (agent alone), no model may generate text.

Create the `uv` environment. Download the base model and the edited model. Record repository revision and file hashes to `results/hashes.txt`. Diff the weights and write `results/diff.md`: which tensors differ, how many weights changed (expected 131,072, in the MLP output weights of layers 15 and 19, 64 columns each), the stored precision (dtype) of the published weights, and the size of the changes.

The answer records: where the models are on disk, the dtype, and whether the edit is where the MIT post says it is.

## Answer

Resolved 2026-11-12. No model generated text.

- Environment: `uv` project, Python 3.12, `pyproject.toml` and `uv.lock` committed. Run scripts with `uv run python -I ...`.
- Models on disk: `models/base` (`Qwen/Qwen3.5-0.8B` @ `2fc06364715b967f1860aea9cf38778875588b17`) and `models/edited` (`RikiyaT/Qwen3.5-0.8B-weight-space-programming` @ `d1671a178705bcab7644806d23c535517f35723b`). Hashes in `results/hashes.txt`; the weight files' hashes match those listed by Hugging Face.
- Stored precision: bfloat16 (16-bit) for 873,436,192 of 873,438,784 weights. "Full precision" in this project means BF16.
- The edit is where the MIT post says: exactly two tensors differ, `down_proj.weight` of the MLPs in layers 15 and 19, 64 of 3,584 columns each. 131,072 weights are in those columns; 130,188 actually differ. Both tensors match the sha256 values on the model card. Details in `results/diff.md`, script `src/diff_weights.py`.
- Size of the edit: 10.64% and 8.11% of each whole tensor; 85% and 62% of the touched columns. The change in each tensor is a single direction. So the edit is narrow but large where it lands.
- The edited model's repo also contains the authors' own per-question outputs (`models/edited/eval/`), not opened here.
