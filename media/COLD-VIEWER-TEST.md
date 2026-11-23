# Cold-viewer test for the post video

The video passes only if people who know nothing about this project can say what it showed.

## Who

Three people who have not seen the project, the repo or the explainer. At least one of them should not work in tech.

## How

1. Send `post-video.mp4` to their phone, or hand them yours. **Sound off.** Play it once. Don't explain anything first, and don't let them rewind.
2. When it ends, ask these questions in this order. Write the answers down word for word. Don't correct them or hint.
   1. "What did it say?"
   2. "Did the fix survive being compressed? How do you know?"
   3. "Did the model stay as good? Compared with what?"
   4. "What did the amber squares mean? The teal lines? The dashed line?"
   5. "Was anything too fast, too small, or confusing?"
3. Note where they frowned, squinted or leaned in.

## Pass

All three say, in their own words, both halves: **the fix survived** (it still loops far less) **and the accuracy didn't** (fewer right answers). Any answer that gives only one half is a fail for that viewer.

If anyone fails, write down what they said instead. The fix goes in the video, not in an explanation to them.

## Already done (proxy, not people)

Two fresh AI agents with no context watched the muted video at 2 frames a second (2026-11-23).

- **Round 1** missed that the fix survived. Its other notes: amber meant two things, the similarity numbers were unexplained, and the original model's score was missing. All three were fixed.
- **Round 2** got both halves. Its remaining notes were also fixed: a wording clash about the layers, a count lagging behind the knob, a clipped label, and an end card that was too dense.

A model is not a phone viewer: it doesn't see motion, and it reads more carefully than someone scrolling a feed. This test is still open until three people have done it.
