# Weight edit vs quantization

Measures whether a published weight edit that stops a small model from looping still works after the model is quantized.

## Language

**Base model**:
The unedited `Qwen/Qwen3.5-0.8B` as published.
_Avoid_: original, vanilla, stock model

**Edited model**:
`RikiyaT/Qwen3.5-0.8B-weight-space-programming`: the base model with the MIT authors' 131,072-weight change applied. Downloaded as published, never changed here.
_Avoid_: fixed model, patched model, our model

**The edit**:
The MIT authors' weight change that separates the edited model from the base model.
_Avoid_: the fix (use only for its effect), the patch, fine-tune

**Precision level**:
How many bits store each weight: full, 8-bit or 4-bit.
_Avoid_: size, compression level

**Version**:
One model at one precision level. There are six: base and edited, each at full, 8-bit and 4-bit.
_Avoid_: variant, build, model (when a specific precision is meant)

**Quantization**:
Storing every weight of a model with fewer bits, which rounds each weight slightly. Same model, smaller file; not a different or smaller model.
_Avoid_: shrinking, distilling, smaller model

**Looping**:
A response that reaches the token limit without giving a final answer. Measured as a rate over the question set.
_Avoid_: repetition (a response can hit the limit without literally repeating)

**Reduction in looping**:
At one precision level, the base model's looping rate minus the edited model's looping rate.

**Survives**:
The edit survives a precision level when the reduction in looping there is at least half of the reduction at full precision.
_Avoid_: works, holds up

**Baseline**:
A run of the base model with a settings-only change (thinking off, or a repetition penalty) and no edit, to show what settings alone achieve.
_Avoid_: control (the base model at default settings is the comparison, not a baseline)
