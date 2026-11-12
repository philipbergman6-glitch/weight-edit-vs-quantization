# Restate what this repo adds

Type: grilling
Status: resolved
Blocked by: none
Map: [does the edit survive quantization?](../map.md)

## Question

The prior-work re-check ([Re-check the prior-work claims and MIT's exact test procedure](02-prior-work-and-mit-procedure.md)) found that the README's "still open" claim is out of date: a 500-question full-precision vs 4-bit comparison of the edited model already exists (TurinTech, calibrated Q4_K_M, accuracy 46.95% vs 45.20%, same share at the token limit), and the thinking-off baseline has been measured by others. It also found the edit is not small per weight (the edited tensors change by about 8 to 11%).

Decide with Philip:

- What does this repo claim to add now? Candidate: base and edited at all three precision levels on one stack, so the reduction in looping is computed per precision level, with 8-bit and a stock 4-bit file, which nobody has published.
- Is the question still worth a two-minute interview point, and how is it worded honestly given the 4-bit answer is partly known?
- Which README lines get corrected (the six corrections listed in ticket 02's answer), and does Philip make those edits or approve them?
- Does knowing TurinTech's result change how the prediction is written? (It must be stated in the prediction that this result was known.)

## Answer

Resolved 2026-11-12 with Philip (yes to all four recommendations).

- **What the repo adds:** the base model and the edited model side by side at full precision, 8-bit and a stock (uncalibrated) 4-bit file on one setup, so the reduction in looping is measured at each precision level. Not claimed: being the first 4-bit test of the edit.
- **Continue:** yes. The honest story includes "I re-checked the prior work, found my gap claim out of date and narrowed it."
- **README corrections:** drafted by the agent, approved by Philip as a diff before commit.
- **Prediction:** `PREDICTION.md` must state that TurinTech's 4-bit result (46.95% vs 45.20%, same share at the token limit) was known when it was written.
