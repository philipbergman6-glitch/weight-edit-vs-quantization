# Download both models, record hashes, diff the weights, confirm the edit

Type: task
Status: claimed
Blocked by: none
Map: [does the edit survive quantization?](../map.md)

## Question

Manual work (agent alone), no model may generate text.

Create the `uv` environment. Download the base model and the edited model. Record repository revision and file hashes to `results/hashes.txt`. Diff the weights and write `results/diff.md`: which tensors differ, how many weights changed (expected 131,072, in the MLP output weights of layers 15 and 19, 64 columns each), the stored precision (dtype) of the published weights, and the size of the changes.

The answer records: where the models are on disk, the dtype, and whether the edit is where the MIT post says it is.
