# Re-check the prior-work claims and MIT's exact test procedure

Type: research
Status: claimed
Blocked by: none
Map: [does the edit survive quantization?](../map.md)

## Question

The README's prior-work section is marked second-hand. Re-check each claim in it against primary sources, starting with the two PDFs in `reading/` (the MIT post and arXiv 2611.09382) and the edited model's Hugging Face page.

1. MIT's exact evaluation procedure for Qwen3.5-0.8B: precision, runtime, sampler, token limit, thinking mode, number of questions, number of runs per question, how a response is counted as looping or failed, how answers are graded, and what "50 forward passes" refers to.
2. What quantization tests of this edit already exist: who, which precision levels, which tool, how many questions, what result. Is "one clean comparison at 200+ questions" still an open gap?
3. The criticisms: thinking off recovers most of the gain; results swing with sampler settings; "ordinary steering". Who said each, with what numbers?
4. The three cited papers (arXiv 2410.16454, 2406.11717, 2606.10154): does each say what the README says it says?

Mark every claim as confirmed, corrected (with the correction) or not found.
