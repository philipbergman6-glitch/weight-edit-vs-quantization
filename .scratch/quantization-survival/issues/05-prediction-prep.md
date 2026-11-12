# Prediction prep: what should Philip expect, and why?

Type: grilling
Status: resolved
Blocked by: 04, 09
Map: [does the edit survive quantization?](../map.md)

## Question

A teaching and grilling session so Philip can form his own prediction. Explain in plain words what rounding does to a small weight change, and lay out the evidence on both sides (the unlearning result where 4-bit undid the change; directional edits that reportedly survive 4-bit). Then Philip states what he expects at 8-bit and at 4-bit and why. Challenge the reasoning; do not supply the answer or the wording.

Resolved when Philip can say his prediction and his reason out loud.

## Answer

Resolved 2026-11-12. Covered: what rounding does (allowed values per precision level), when rounding erases a change (change smaller than the gap), the evidence both ways, and two failure types (the edit itself blurred; the rest of the model disturbed). Philip stated his prediction and reason himself: survives at 8-bit, does not survive at stock 4-bit, because he expects rounding to erase the edit itself.
