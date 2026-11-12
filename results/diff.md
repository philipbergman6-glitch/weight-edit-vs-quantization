# Weight diff: base model vs edited model

Produced by `src/diff_weights.py`. Only stored weights were read; no model was run.

- Base file: `models/base/model.safetensors-00001-of-00001.safetensors`
- Edited file: `models/edited/model.safetensors-00001-of-00001.safetensors`
- Tensors compared: 488, all with matching names, shapes and dtypes
- Total weights: 873,438,784
- Stored precision: torch.bfloat16 (873,436,192 weights), torch.float32 (2,592 weights)
- Tensors that differ: 2
- Weights that differ: 130,188 (0.0149% of all weights)

## Tensors that differ

### `model.language_model.layers.15.mlp.down_proj.weight`

- Shape: (1024, 3584), dtype torch.bfloat16
- Weights changed: 65,260
- Columns touched: 64 of 3584 (indices [0, 2, 11, 25, 34, 35, 38, 39]...)
- Rows touched: 1024 of 1024
- Size of change relative to the whole tensor (norm of change / norm of tensor): 10.64%
- Largest single change: 0.146362
- Mean absolute change, changed weights only: 0.003722
- Mean absolute base value, changed weights only: 0.005926
- Mean absolute base value, whole tensor: 0.006563

### `model.language_model.layers.19.mlp.down_proj.weight`

- Shape: (1024, 3584), dtype torch.bfloat16
- Weights changed: 64,928
- Columns touched: 64 of 3584 (indices [1, 5, 8, 11, 13, 15, 17, 18]...)
- Rows touched: 1023 of 1024
- Size of change relative to the whole tensor (norm of change / norm of tensor): 8.11%
- Largest single change: 0.214844
- Mean absolute change, changed weights only: 0.002954
- Mean absolute base value, changed weights only: 0.006628
- Mean absolute base value, whole tensor: 0.007055
## Extra checks (run once inline on 2026-11-12, not by the script)

- The sha256 of the raw bfloat16 bytes of both edited tensors matches the values published on the edited model's card:
  layer 15 `82e2d733ea64feaeb4af93a1e065641d3df98b494a8b7576ef2f52e90fe2ee53`, layer 19 `8ef3c61bc36af113ad58e89dbb0a4a14dcba5a45cb750c15ab515c82ddd12eb2`.
- 131,072 weights sit in the touched columns (2 tensors x 64 columns x 1,024 rows). 130,188 of them actually differ; the other 884 (276 in layer 15, 608 in layer 19) round to the same bfloat16 value.
- The change in each tensor is one direction: its largest singular value holds 99.999% of the change's energy (1.7489 vs 0.001 next in layer 15; 1.3988 vs 0.0009 in layer 19).
- Within the 64 touched columns the change is large: its norm is 85% (layer 15) and 62% (layer 19) of those columns' norm before the edit. The columns' norm grows from 2.058 to 2.505 (layer 15) and from 2.247 to 2.521 (layer 19).
