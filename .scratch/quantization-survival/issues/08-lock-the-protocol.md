# Lock the protocol: settings, baselines, scoring, minimum run

Type: grilling
Status: open
Blocked by: 02, 03, 07
Map: [does the edit survive quantization?](../map.md)

## Question

Decide, with Philip, everything the run needs:

- Token limit (MIT used 32,768) given the time budget from the speed test.
- Sampler settings and seed, identical for every version; one response per question or several.
- Which questions: source, how many, how chosen.
- Exactly what 8-bit and 4-bit mean in the chosen tool.
- The two baselines on the base model: how thinking is turned off; which repetition penalty value.
- How a response is scored as looping, and how accuracy is graded.
- How uncertainty is reported with the numbers.
- The guaranteed minimum run: the smallest run that still answers the question and is certain to finish by Sat 2026-11-14, and the order in which runs happen so the most important rows finish first.

Resolved when the spec can be written with nothing left to choose.
