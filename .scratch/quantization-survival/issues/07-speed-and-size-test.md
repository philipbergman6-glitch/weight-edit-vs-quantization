# Speed test, with file size and memory per version

Type: task
Status: open
Blocked by: 01, 04, 06
Map: [does the edit survive quantization?](../map.md)

## Question

Manual work (agent alone). Using the toolchain chosen in ticket 01, build what is needed and measure on this laptop, per precision level: file size on disk, memory used while running, and tokens per second. Use a neutral prompt, not benchmark questions, and do not report how often anything loops.

The answer records the numbers and a time budget: how long 200 questions take per version at token limits of 32,768, 16,384, 8,192 and 4,096 if every response ran to the limit.
