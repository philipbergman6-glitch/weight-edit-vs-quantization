# "AI improving AI"? Recursive self-improvement and the weight edit, checked against primary sources

Question: is it honest to frame the MIT weight edit (and this repo's quantization test of it) as "we are getting closer to recursive self-improvement"?
Checked: 2026-11-22. No model was downloaded or run for this note.

Labels used below:

- **STATED**: the source says it, quoted with location.
- **INFERRED**: my reading of what the source implies. Not a quote.
- **UNVERIFIED**: seen only in a search-result summary or a secondary write-up. Not read at the source.
- **CONFIRMED / CORRECTED / NOT FOUND**: verdict on a claim.

Source IDs like [S3] point to the list at the end. Expected output, fixed before reading: an answer to each of the five questions from the brief, each claim tied to a quote, plus a list of what can and cannot be said in public. Success criterion: every "over-claim" verdict rests on a quoted primary source, not on my opinion.

---

## 1. What changes for us

1. **The authors themselves name recursive self-improvement, but only as a possible future, not as a result.** It is one of five bullets under "What Comes Next?" [S1]. So linking the two is not invented. Presenting it as something the edit *shows* would go beyond what the authors claim.

2. **The same post contains the strongest argument against the framing.** On a model that does not loop, the editor could not improve anything: "Editing weights could remove an obstacle that hid an ability, but it could not add an ability the model lacked" [S1]. Recursive self-improvement needs capability to go up. This edit removes one fault.

3. **New since 12 Nov: a preprint claims a model edited its own weights.** Fan et al., "Language Models Can Rewrite Their Own Weights", arXiv 2611.21885, 16 Nov 2026 (v2 18 Nov) [S6]. Qwen3.5-27B, +6.6 points on 490 held-out maths problems. It calls this "a necessary step toward recursive self-improvement". It is six days old, not peer reviewed, and I found no independent replication. By its own text each session starts from the base weights, so gains are not stacked, and the best edit works by cutting token-limit hits. A LinkedIn post that talks about self-improvement and does not mention this paper will look uninformed; one that cites it as proof will over-claim.

4. **New criticism that touches this repo's result: the edit may depend on the sampler.** One independent evaluator reports that under greedy decoding with no presence penalty the MIT edit scores 5% with 95% of answers at the token limit, against 52% and 28% under the published sampler [S4, discussion #5]. Single source, by the author of a competing edit, and it changes two settings at once. This repo ran every row with presence penalty 1.5 and temperature 0.6 (`results/table.md`). INFERRED: "the reduction in looping survives quantization" is a statement about that sampler. It was not tested without the penalty.

5. **The "still open" gap in the README is still open, as far as I could find.** No one has published base and edited models side by side at full precision, 8-bit and a stock 4-bit file since 12 Nov. See section 3.

6. **The authors answered the thinking-off criticism on 12 Nov.** "Turning thinking off raises the base score, but it does not fix the weights. It avoids the loops by not using the mode that has them" [S1]. The README lists the criticism but not the reply.

7. **Three new papers weaken the "a frontier model was needed" reading.** A sort over neuron statistics matches a re-derived (linear-program) version of the edit ("the edit acts as a nearly constant bias along u") [S9]; a search with "zero LLM tokens" beats it (54.6% against 51.7%) [S10]; Claude finds a different fix that scores higher (58.1%) [S11]. INFERRED: what is specific to the LLM is finding the fault without being told where to look, not the edit itself.

---

## 2. Q1: what the authors claim and do not claim

All quotes from the live blog post [S1], fetched 2026-11-22. The post has no section called "Limitations". The closest are "What Comes Next?" and "Response to Comments" (the latter "Added November 12, 2026").

### What they claim

| Topic | Quote | Location |
|---|---|---|
| Headline | "We find that frontier LLMs are surprisingly good at natively reading and writing neural network weights much like code" | TL;DR |
| Strength of claim | "These results show sparks of Weight-Space Programming ... This might be a big deal for both optimization and interpretability." | TL;DR |
| The Qwen edit | "asked to make Qwen3.5-0.8B better at math without gradients, Astra identifies an issue in its weights causing reasoning loops that Qwen's own model card warns about, and fixes this by natively editing 0.016% of the weights" | TL;DR |
| Outlook | "We believe this marks the beginning of a dramatic shift in fields like mechanistic interpretability and neural network optimization." | What Comes Next? |

### The only mention of recursive self-improvement

STATED, complete bullet, under "What Comes Next?", introduced by "Here are some examples" of "radical new possibilities":

> "Recursive self-improvement: Today, recursive self-improvement is often operationalized as a model writing code that launches training jobs. An LLM that can inspect, debug, and improve its own weights, or those of a newer model, offers a richer, more native path to it."

INFERRED: this is conditional ("An LLM that can ...") and sits in a list of future possibilities next to "one-shot model initialization" and "True architectural and model merging". No experiment in the post has a model edit itself or a newer model. In every experiment the editor (GPT-6 Astra) is far larger than the network it edits. Full-text search of the post: "recursive" occurs only in this bullet; "self-improv" only here; "AI improving AI" does not occur.

### What they do not claim, in their own words

| Topic | Quote | Location |
|---|---|---|
| Not a capability gain | "Fixing loops, however, is not the same as making a model better at math: it lets the model finish answers it could already work out." | "Raising math capability of a model that does not loop" |
| Negative result | "Here, Astra could not improve it ... none moved MATH-500 by more than about a point, a gain Astra itself reported as not established. Editing weights could remove an obstacle that hid an ability, but it could not add an ability the model lacked." | same section (Gemma 3 270M: 6.8% base, 7.0 to 7.7% edited) |
| Limited | "Our current results do show that capabilities are exciting but still limited, specifically due to inefficiencies in context length and harnesses." | What Comes Next? |
| Not a method | "Weight-Space Programming is not a method. It is the name of an emerging concept ... Its experiments are evidence for that statement, not a proposed method for editing or training networks." | Response to Comments |
| Not better than baselines | "The baselines here are not there to rank methods against each other on equal terms ... It showed a new capability, which at the time was still weak and unreliable on many tasks." | Response to Comments |
| Not beyond human experts | "We have not compared Astra with interpretability researchers, and we have no reason to believe it would beat every one of them at any particular skill." | Response to Comments |
| Thinking-off | "Turning thinking off raises the base score, but it does not fix the weights. It avoids the loops by not using the mode that has them." | Response to Comments |

Cross-check by two independent readers: Ashish Kumar, 3 Nov 2026: "The report lists recursive self-improvement as a direction, not a result." and "None is a model improving itself." [S16]. Brainwagon, 8 Nov 2026: "As for all the talk of recursive self-improvement, what was demonstrated was a very large model fixing a known bug in a model with fewer than a billion parameters." [S17].

---

## 3. Q2: what is new since 2026-11-12

### Status of the original work

| Item | Finding | Evidence |
|---|---|---|
| Retraction or correction | NOT FOUND | The post is live; the only dated change is the "Response to Comments" section, "Added November 12, 2026" [S1] |
| Full paper by the MIT authors | NOT FOUND | arXiv author search for the first author lists nothing after 2 Oct 2026 [S2]. The post says: "We are currently building a benchmark and a harness" [S1] |
| Edited model | unchanged | Hugging Face API: last modified 2026-11-02, revision `d1671a17...`, the same revision the earlier note used [S3] |
| Authors' GitHub issues | no new issues | Newest issue is #11, opened 2026-11-09 [S5] |
| Model page discussions | two new: #5 (17 Nov), #6 (18 Nov) | [S4] |
| Follow-up papers | 33 arXiv entries match "weight-space programming", 3 Nov to 19 Nov | [S2]. The authors say "more than a hundred" replications and extensions are known to them [S1] |

### New quantization tests of the released edit

**NOT FOUND.** Checked: the model's discussion tab, its "quantized" derivative listing (5 repositories, none newer than 6 Nov), a Hugging Face search for the model name (40 repositories), the authors' GitHub issues, the arXiv list above (no title on quantization), Hacker News (Algolia search, 18 stories) and web search [S3, S4, S5, S2, S15]. What exists:

| Who, when | What | Why it does not close the gap |
|---|---|---|
| NeoCortex, 20 Nov [S4 #6] | MIT's edit on a q8_0 file: "82 of 140 with thinking, 63 of 140 without"; unedited model "5 of 50 with thinking" | 8-bit only. No full-precision cell on the same stack, no 4-bit |
| NeoCortex, 18 Nov [S4 #5] | A *different* edit (SGNE-CC) on q8_0: 22 of 50 correct, 4% at the cap; unedited 5 of 50 | Different edit. Its author compares this with his own BF16 run on another stack and concludes "neither switching the inference stack to llama.cpp nor 8-bit quantization breaks the effect". INFERRED: two stacks, two problem sets, so this is not a controlled comparison |
| JonathanColetti card [S18] | ONNX builds: int8 "100%", 4-bit "~69%" in a column "Agrees with bf16" | STATED footnote: "Next-token argmax agreement with the PyTorch model over a 35-token prompt (spot check)". One prompt. Not a benchmark |
| qxlsz MLX [S19] | re-read today: "On the same 40 problems it hit the limit on 27.5%, so loops stayed reduced, but it solved 12 against 21 for this model." | Already in the README. Unchanged |

Verdict on the README's "I found no published run of the base model at each precision, no 8-bit comparison and no stock 4-bit test above 40 questions": **still CONFIRMED as of 22 Nov**, with the usual limit that X, Reddit and Discord were reached only through web search.

### New criticism and replications

| Line of criticism | New evidence since 12 Nov | Source |
|---|---|---|
| Thinking-off matches it | "unedited: 43.6% / edited: 45.2%" with thinking off, 8,192 tokens. "So most of the gain is that the edited model stops looping; with thinking off, the unedited model gets almost as far." Also: "A random edit of the same size, on 100 problems, scores 19%; your edit scores 51%. So the direction the agent found matters." | [S4 #6], hedwigai, 18 Nov; write-up [S20]: "The short answer is that the edit stops a loop. It adds very little math." |
| Sampler sensitivity | T = 0, presence penalty 0: base 0% / MIT edit 5% accuracy, 100% / 95% at the 32K cap. T = 0.6, presence penalty 1.5: 8% / 52% and 92% / 28%. Full MATH-500, PyTorch BF16. Caveat by the poster: "the two regimes change sampling (T = 0 vs. T = 0.6, top_p = 0.95, top_k = 20) together with presence_penalty" | [S4 #5], Nondual-Observer, 17 Nov. Single source; the poster is the author of the competing edit |
| "It is a constant bias / a steering vector" | "The outcome is that, on this model, the edit acts as a nearly constant bias along u." A sort over 8 neurons scores 67.0% against 67.4% for the LP edit on 1,000 problems | [S9] Fischetti, arXiv 2611.21432, 16 Nov (this studies the LP re-derivation in [S21], not the released tensors) |
| No LLM needed for the edit itself | "Tree-Ising achieves 54.6% on MATH-500, outperforming the agent's edit (51.7%) ... It requires only four forward-pass requests and zero LLM tokens". Also cites the cost of the original: "158 agent turns, 89.7 million tokens, and 50 forward-pass requests" | [S10] arXiv 2611.14210, 10 Nov |
| Other editor, other fix | Claude Opus 5.5 "raised MATH-500 from 6.7% to ... 58.1% ... Unlike the original, which removed an internal loop direction, every edit acted at the output: it scaled the final norm, raising the effective sampling temperature, and lowered the logit of 'Wait' while raising that of </think>." "On Gemma 3 270M, which rarely loops, no edit helped (-0.8 points), as in the original." | [S11] arXiv 2611.20953, 16 Nov |
| Reading weights is shallow | "LLMs can read and write small networks, but that this currently amounts to compiling hand-designed programs and reading the layout of the input layer." | [S12] arXiv 2611.21449, 16 Nov |
| Reading weights leans on memory | "zero-shot weight reading by this model is better described as local arithmetic plus dataset priors than as weight-flow tracing" ("exploratory results from mostly single runs") | [S13] arXiv 2611.08070, 5 Nov |
| Written networks are hand-built programs | "it is a 15-line Python program built from standard gates"; "not a sign of something beyond what we'd expect from humans or conventional algorithms" (read through a page summary) | [S22] Cyera, 16 Nov |
| Knowing vs committing | "at T = 0 the unedited model has a correct value in its thinking in 41 % of problems and commits to none of them." "Without the thinking block, the same model is strong: 58 / 48 / 46 of 100 fresh problems" | [S4 #4], NeoCortex report v0.5, 21 Nov |

INFERRED from the last three weeks as a whole: independent work keeps confirming that the edit reduces looping under the published sampler, and keeps narrowing what that means. The base model already contains the answers; the edit (or switching thinking off, or a bias, or a temperature change) lets it stop and say them.

---

## 4. Q3: what "recursive self-improvement" means, and what has been shown by 2026

### Definitions

| Source | Quote | What it requires |
|---|---|---|
| I. J. Good, 1965 [S23] | "Since the design of machines is one of these intellectual activities, an ultraintelligent machine could design even better machines; there would then unquestionably be an 'intelligence explosion', and the intelligence of man would be left far behind." | The machine already surpasses humans at designing machines, and the designs keep getting better |
| Schmidhuber, Gödel machine, 2003 [S24] | "such a problem solver rewrites any part of its own code as soon as it has found a proof that the rewrite is useful" | Self-reference (it rewrites itself, including the rewriting part) and a guarantee that each rewrite helps |
| Yudkowsky, 2008 [S25] | "Recursion that can rewrite the cognitive level is worth distinguishing." And the warning that one rewrite is not a loop: "If you're a recursified optimizing compiler, you rewrite yourself just once, get a single boost in speed (like 50% or something), and then never improve yourself any further, ever again." | The improvement must feed back into the ability to improve, repeatedly. A one-off boost does not count |
| Anthropic, 2026 [S26] | "an AI system capable of fully autonomously designing and developing its own successor. This is called recursive self-improvement." | Full autonomy; a successor, not a patch |

Good's wording was checked at Wikiquote, which cites the 1965 paper; I did not read a scan of the original. Yudkowsky's compiler sentence is the closest historical description of a one-off fix like the MIT edit.

### What has been demonstrated

| Work | What it shows (STATED) | What it does not show |
|---|---|---|
| RE-Bench, METR 2024 [S27] | "the best AI agents achieve a score 4x higher than human experts when both are given a total time budget of 2 hours per environment. However, humans currently display better returns to increasing time budgets ... achieving 2x the score of the top AI agent when both are given 32 total hours" | A benchmark of research engineering tasks. No self-improvement |
| AI Scientist, 2024 [S28] | "the first comprehensive framework for fully automatic scientific discovery ... In principle, this process can be repeated to iteratively develop ideas" | "In principle". It writes papers; it does not improve itself |
| Darwin Gödel Machine, 2025 [S29] | "a self-improving system that iteratively modifies its own code (thereby also improving its ability to modify its own codebase) ... increasing performance on SWE-bench from 20.0% to 50.0%" | The model is not changed: "this paper focuses on improving the design of coding agents with frozen pretrained FMs". Only the scaffolding around it improves |
| AlphaEvolve, 2025 [S30] | "accelerated the training of the LLM underpinning AlphaEvolve itself" | One loop-back in a human-run pipeline. No claim of compounding |
| Anthropic, "When AI builds itself", 2026 [S26] | "As of May 2026, more than 80% of the code we merge into Anthropic's codebase was authored by Claude." | "We are not there yet, and recursive self-improvement is not inevitable." "large performance gaps persist when it comes to Claude exercising judgement in choosing goals" |
| OpenAI, "Research acceleration", 6 Sep 2026 [S31] | "we have now reached the goal ... of having an automated research intern ... a system that can carry out well-defined research tasks under human direction" | "agents still require significant human steering to be successful, especially as task complexity rises." "they do not mean that rapid RSI is necessarily an outcome we should pursue." |
| METR assessment of Anthropic, 5 Nov 2026 [S32] | "Anthropic is likely improving the capabilities of their models on well-specified tasks at around twice the rate they did between March 2024 and October 2025. This estimate is given with high uncertainty"; "We guess that a majority (perhaps ≈80%) of the current (October 2026) acceleration is due to AI." | "AI is not yet able to make highly significant and fully autonomous contributions to the most important parts of the model training process." "R&D is accelerated primarily via AI assistance rather than fully autonomous contributions". METR adds that the public "has to rely on METR's judgment much more than would be ideal" because evidence was redacted |
| METR capability update, 20 Nov 2026 [S33] | "time horizons are doubling roughly every 3.6 months"; "up to 27 hours on the verifiable subset" | "current public evidence is insufficient to rule out drastic AI R&D acceleration in the next couple of years"; "we do not see strong acceleration or deceleration in model ability over the public frontier"; weakness in judgment is a "reasonable candidate" for what delays it |
| Fan et al., self-rewriting, 16 Nov 2026 [S6] | "its own edit makes it 6.6 points more accurate on problems it never saw" (57.2% to 63.8%, token-limit hits 33.6% to 26.1% [S4 #5]) | See below |

UNVERIFIED, from search summaries only: a 12 Sep 2026 statement attributed to Anthropic's CEO that recursive self-improvement "is starting to happen across the industry"; a DeepMind position (I found no primary DeepMind statement); OpenAI's March 2028 target for an "automated AI researcher".

### The self-rewriting preprint, read sceptically

STATED [S6]: "to our knowledge for the first time, a language model rewrites its own weights by its own reasoning and becomes better, with no gradients and no training." "We believe self-rewriting is a necessary step toward recursive self-improvement". Its conclusion says "an improved model can be set to work on itself again, a path toward recursive self-improvement. That path should be taken with people in the loop".

What limits it, from its own text:

- **Not stacked.** "the model in use gets better as its sessions accumulate, each starting from the base weights" and "each edit it submits replaces the last". INFERRED: eight tries from the same starting point, best one kept. That is repeated search, not improvement built on improvement. The edited model was not shown to be a better editor.
- **Same kind of fix as MIT's.** "The larger gain comes from one uniform change: it raises the time-step bias of every linear-attention layer by 0.5, and with it fewer of its answers run out of tokens." A commenter on the model page notes the fall in cut-offs (-7.5 points) "matches the scale of the accuracy gain (+6.6 pp)" [S4 #5]. INFERRED: again a model that finishes more answers, not shown to reason better.
- **Mostly no edit.** "it withdraws in five and submits in three". Smaller models fail: "the 2B model made no edit", "4B and 9B models break themselves".
- **A human-built frame decides what counts.** The framework supplies the task, the tools, the graded practice problems and a reserved check before submission.
- **One model family, one task type, not replicated, not reviewed.** I found only descriptive press coverage. No thinking-off baseline was run ("A comparison with thinking disabled would be a separate experiment at 27B", author's comment [S4 #6]).

### Where the lines are

| Level | Example | Status in Nov 2026 |
|---|---|---|
| A. AI assists human AI research | Coding agents at the labs; METR's "around twice the rate" | Demonstrated, measured with wide uncertainty |
| B. AI improves the scaffolding around a frozen model | Darwin Gödel Machine | Demonstrated on coding benchmarks |
| C. AI changes another, smaller model's weights to fix a fault | MIT edit and its many replications | Demonstrated and replicated |
| D. A model changes its own weights and scores better once | Fan et al. | Claimed in one preprint, unreplicated |
| E. Each improved version produces a better next version, without humans choosing goals or judging results | Good, Yudkowsky, Anthropic's definition | Not demonstrated by anyone. The labs say so themselves |

The MIT edit is level C. This repo's measurement says a level-C fix survives compression for looping under one sampler. Neither is evidence about level E.

---

## 5. Q4: which ingredients the MIT edit has, and which it lacks

| Ingredient of recursive self-improvement | MIT edit | Evidence |
|---|---|---|
| Same system edits itself | No. GPT-6 Astra edits Qwen3.5-0.8B, a different and far smaller model | [S1]; Fan et al.: "There the editor is a much stronger model than the one it edits, and a model that edits its own weights is named only as a direction for future work" [S6] |
| Closed loop without humans | No. Humans chose the model, the goal ("make Qwen3.5-0.8B better at math"), the 50-pass budget and the evaluation | [S1] |
| Raises general capability | No. "it lets the model finish answers it could already work out"; on Gemma "it could not add an ability the model lacked" | [S1] |
| Improvement helps the next round of improving | No. The edited Qwen is not used to edit anything | [S1] |
| Compounding over rounds | No. One edit, applied once | [S1] |
| AI changes weights by reasoning, no training | Yes | "Astra edits the weights in a Python kernel, with no training" [S1] |
| AI found the fault itself | Yes, with forward passes on practice problems; a known fault ("that Qwen's own model card warns about") | [S1] |
| Effect is real and replicated | Yes, under the published sampler | earlier note, `research/prior-work-and-mit-procedure.md` |

INFERRED: one of the five defining ingredients is partly present (an AI writes weights), four are absent.

### Relation to known techniques

| Technique | What it does | Relation to the edit |
|---|---|---|
| Refusal-direction ablation, Arditi et al. 2024 [S34] | Finds one direction in activations and removes it from the weights | The same kind of change (a single-direction weight change), aimed at looping, but not a pure removal: in the released edit the touched columns get larger (combined norm 2.058 to 2.505 and 2.247 to 2.521, `results/diff.md`), and the authors say the direction was "subtracted" [S1]. The post cites Arditi for this step. Kumar: "The operation is abliteration's operation." but "Nobody had a recipe for Qwen3.5-0.8B's loop." [S16]. Goedecke: "basically the Heretic abliteration playbook", something "a competent human researcher could have and would have done" [S35] |
| Activation steering, Turner et al. 2023 [S36] | "contrasts the intermediate activations on prompt pairs ... to compute a steering vector", added at inference | A steering vector along the same direction works about as well (earlier note; [S9] gives the reason: the edit acts as a near-constant bias) |
| ROME / MEMIT, Meng et al. 2022 [S37] | "modify feed-forward weights to update specific factual associations using Rank-One Model Editing" | Same shape (rank-one change to an MLP output matrix), different target: one fact, located and solved for by a human-designed algorithm with gradients |
| Mechanistic interpretability | Humans trace what parts of a network compute | The post places itself here: Weight-Space Programming "will succeed partly by composing and improving techniques from human interpretability research" [S1] |

Is it new or a rebrand? STATED by the authors: "What is new here is a general-purpose frontier model, used as it is, that reads and writes the weights themselves" [S1]. INFERRED verdict: the edit is a known operation; what is new is who did it and with how little guidance. Later work shows the edit can be reproduced with no LLM at all once the recipe is known [S9, S10]. "Rebrand" is fair for the edit, unfair for the claim the authors actually make, which is about the editor.

---

## 6. Q5: quantization and edits, short

Figures re-verified today at the source:

| Claim in README | Verdict | Quote |
|---|---|---|
| Zhang et al., ICLR 2025: 21% retained at full precision, 83% after 4-bit | CONFIRMED | "for unlearning methods with utility constraints, the unlearned model retains an average of 21% of the intended forgotten knowledge in full precision, which significantly increases to 83% after 4-bit quantization" [S38] abstract |
| Kadadekar: refusal falls 12 to 68 points while quality holds | CONFIRMED | "9 hidden-danger rows plus 1 near-hidden-danger row show quality stable or improved while refusal falls by 12-68 percentage points" [S39] abstract. The "cosine above 0.97" figure is in section 4.4, verified in the earlier note, not re-read today |

Newer or adjacent:

- Steering under quantization: Makarov, arXiv 2610.40055 (29 Oct 2026) asks whether activation steering "survives INT8 and NF4 quantization" [S40]. Abstract read; the result sentences were cut off in my fetch, so its numbers are UNVERIFIED.
- Unlearning: Turani et al., arXiv 2605.12765: "unlearning through parameter updates is expensive, hard to audit, and can be undone by quantization" [S41].
- Rounding already at 16-bit: Hu et al. (earlier note) and Tree-Ising, which restricts edits to "sign flips and exponent shifts" in BF16 [S10].
- NOT FOUND: any paper testing whether ROME/MEMIT edits or refusal-direction ablation made at full precision survive 4-bit rounding. One search only.

Why a rank-one, large edit should survive rounding (INFERRED, with this repo's own measurements):

1. Zhang's mechanism needs small changes: "quantization is likely to map the weights of the target LLM and the unlearned LLM to the same values" (quoted in the earlier note). Here the change is not small. In the touched columns its mean size is 0.0037 and 0.0030 against a typical weight of about 0.007 (`results/diff.md`).
2. Rough step sizes, my assumption that the largest weight in a block is 3 to 5 times the typical one: an 8-bit step is about 0.0002, so the edit is some 15 steps; a 4-bit step is about 0.003 to 0.004, so the edit is about 1 step. Measured: the stored edit keeps its direction almost exactly at 8-bit (cosine 0.9998) and mostly at 4-bit (0.93 and 0.90) (`results/edit-rounding.md`).
3. Rounding error is spread over all directions; the edit is one direction (99.999% of its energy, `results/diff.md`). Only the small part of the noise that falls on that direction can cancel it.

This explains why the edit is still in the file. It does not explain the accuracy drop, and Kadadekar's point stands: a direction can be intact while behaviour changes.

---

## 7. Not verified

- Good (1965): wording taken from Wikiquote, not from the paper.
- The Amodei statement of 12 Sep 2026, any DeepMind statement, Jack Clark's timeline, OpenAI's 2028 target, METR "Time Horizon 2" details beyond the two quoted sentences: search summaries only.
- Latent Space headline "'Weight Space Programming' cuts Autoresearch out of the RSI loop", the Lanham "yield ratio" essay, MindStudio, PiyushAI, the r/LocalLLaMA thread: search results only. X/Twitter was not reachable directly.
- Fan et al.: abstract, introduction, conclusion and parts of appendices D and E read; not end to end. Affiliations not extracted (the page mentions UIUC).
- The greedy-decoding result in discussion #5: one evaluator, raw outputs not opened.
- Papers [S9] to [S13] and [S40], [S41]: abstracts only.
- Cyera and notesbylex posts: read through an automatic page summary, quotes as returned by it.
- A Hugging Face repository claiming a different edit on a 27B model "persists through Q4_K_M" (Feyd89): search summary only, different model and edit.

---

## 8. What can honestly be said in public

### Defensible

1. **"A large AI model found and fixed a fault in a small one by editing its weights directly, with no training, and many independent groups reproduced it."** Reason: STATED in [S1], replicated (earlier note; [S4], [S11]).
2. **"The fix removes a looping fault; it does not make the model better at maths."** Reason: the authors say so ("it lets the model finish answers it could already work out") and the thinking-off baselines agree [S1, S4 #6].
3. **"The authors name recursive self-improvement as one possible future direction. They do not claim to have shown it, and their own negative result (Gemma) shows the edit could not add an ability."** Reason: exact quotes in section 2.
4. **"In my test the reduction in looping survived 8-bit and stock 4-bit compression, while accuracy dropped: 100 questions, one sampler, one model, one edit."** Reason: `RESULT.md`. The sampler qualifier matters after [S4 #5].
5. **"AI is measurably speeding up AI research at the labs, and one new preprint reports a model improving itself by editing its own weights; no one, including the labs, claims a closed self-improving loop exists."** Reason: [S32], [S26], [S31], [S6].

### Over-claims

1. **"We are getting closer to recursive self-improvement, and this edit shows it."** Reason: the edit has one of five ingredients (section 5). Different system, done once, no capability gain, no loop. Yudkowsky's own example of what is *not* recursive self-improvement is a single one-off boost [S25].
2. **"AI is now improving AI"** as a description of this edit. Reason: "improving" suggests capability. The authors separate fixing loops from "making a model better at math" [S1]; switching thinking off gets nearly the same score with no edit [S4 #6].
3. **"My result shows AI-made improvements are robust enough to deploy / to build on."** Reason: accuracy fell from 61% to 45% and 42% (`RESULT.md`); the effect may vanish without the presence penalty [S4 #5]; 100 questions.
4. **"Models can now rewrite themselves"** stated as settled. Reason: one six-day-old preprint, unreplicated, sessions restart from base weights, three submitted edits in eight sessions, gain tracks fewer cut-offs [S6].
5. **"Only a frontier model could have done this" or "a new kind of technique".** Reason: the edit is a single-direction weight change, the same kind as direction ablation [S34]; a sort over eight neurons and an LLM-free search reproduce or beat it [S9, S10]; the authors themselves say "we have no reason to believe it would beat every one of them" [S1].

A framing that survives all of the above: "A published example of one AI repairing another's weights. I checked whether the repair survives compression. It is a small, real step in AI doing interpretability work; the authors mention self-improvement as a hope, and the evidence so far is about fixing faults, not about getting smarter."

---

## Sources

- [S1] Takehi, Teoh, Zhang, Khattab, "Sparks of Weight-Space Programming", live page: https://rikiyat.github.io/blog/weight-space-programming/ (fetched 2026-11-22, full text extracted and searched; sections TL;DR, "Raising math capability of a model that does not loop", "What Comes Next?", "Response to Comments").
- [S2] arXiv API, query `all:"weight-space programming"` sorted by date, and author query for the first author: https://export.arxiv.org/api/query (2026-11-22).
- [S3] Hugging Face API: https://huggingface.co/api/models/RikiyaT/Qwen3.5-0.8B-weight-space-programming ; derivative listing `base_model:quantized:RikiyaT/Qwen3.5-0.8B-weight-space-programming`; model search "weight-space-programming".
- [S4] Model page discussions, read through the API: #2 https://huggingface.co/RikiyaT/Qwen3.5-0.8B-weight-space-programming/discussions/2 , #4 .../discussions/4 , #5 .../discussions/5 (Nondual-Observer, NeoCortex0815, jiajunfanthu; 17 to 22 Nov), #6 .../discussions/6 (un-seen / hedwigai, NeoCortex0815, jiajunfanthu; 18 to 22 Nov). NeoCortex report v0.5: https://github.com/NeoCortex0815/knowing-is-not-committing , DOI 10.5281/zenodo.24420522 (report itself not opened).
- [S5] Authors' issues: https://github.com/RikiyaT/lm_understand-logs/issues (GitHub API, 11 issues, newest 2026-11-09).
- [S6] Fan et al., "Language Models Can Rewrite Their Own Weights", arXiv 2611.21885v2: https://arxiv.org/abs/2611.21885 , HTML https://arxiv.org/html/2611.21885v2 .
- [S7] Hu et al., arXiv 2611.09382: https://arxiv.org/abs/2611.09382 (abstract re-read; full reading in the earlier note).
- [S8] Zheng and Doubao, arXiv 2611.04268: https://arxiv.org/abs/2611.04268 . Proposes "a minimal recursive self-improvement (RSI) loop for vision"; states "This manuscript is conjectural". No experiments.
- [S9] Fischetti, "Just sort it! A note on the LP behind rank-one anti-loop edits", arXiv 2611.21432: https://arxiv.org/abs/2611.21432 .
- [S10] Salloum and Ali, "Tree-Ising", arXiv 2611.14210: https://arxiv.org/abs/2611.14210 .
- [S11] Kundu, "Same Fix, Different Weights", arXiv 2611.20953: https://arxiv.org/abs/2611.20953 .
- [S12] Goworek et al., arXiv 2611.21449: https://arxiv.org/abs/2611.21449 .
- [S13] Ahmed, arXiv 2611.08070: https://arxiv.org/abs/2611.08070 .
- [S14] WeightBench, arXiv 2611.18553: https://arxiv.org/abs/2611.18553 (abstract; listed for completeness).
- [S15] Hacker News search: https://hn.algolia.com/api/v1/search_by_date?query="weight-space programming"&tags=story .
- [S16] Ashish Kumar, 3 Nov 2026: https://ashishkumar.ai/blog/weight-space-programming/ .
- [S17] Brainwagon, 8 Nov 2026: https://brainwagon.org/blog/2026-11-08-a-skeptical-look-at-weight-space-programming.html .
- [S18] JonathanColetti card: https://huggingface.co/JonathanColetti/Qwen3.5-0.8B-Astra-WeightEdit ("Which dtype to pick").
- [S19] qxlsz MLX card: https://huggingface.co/qxlsz/Qwen3.5-0.8B-weight-space-programming-mlx .
- [S20] hedwigai, "Does a weight edit teach Qwen3.5-0.8B math, or stop it looping?": https://www.hedwigai.com/blog/weight-edit-math-or-loops .
- [S21] nathanrs, "Can a Linear Program Do Weight-Space Programming?": https://nathan.rs/posts/weight-space-lp/ (not re-read; see earlier note).
- [S22] Cyera Research, 16 Nov 2026: https://www.cyera.com/research/sparks-of-weight-space-programming-or-just-exploit-engineering ; Lex Toumbourou, 18 Nov 2026: https://notesbylex.com/weight-space-programming-1990s .
- [S23] I. J. Good, "Speculations Concerning the First Ultraintelligent Machine", Advances in Computers 6, 1965, p. 33; text via https://en.wikiquote.org/wiki/I._J._Good ; page reference via https://quoteinvestigator.com/2022/01/04/ultraintelligent/ .
- [S24] Schmidhuber, "Goedel Machines", arXiv cs/0309048: https://arxiv.org/abs/cs/0309048 (abstract).
- [S25] Yudkowsky, "Recursive Self-Improvement", 2008: https://www.lesswrong.com/posts/JBadX7rwdcRFzGuju/recursive-self-improvement .
- [S26] Favaro and Clark, "When AI builds itself", Anthropic Institute, 2026: https://www.anthropic.com/institute/recursive-self-improvement .
- [S27] Wijk et al., RE-Bench, arXiv 2411.15114: https://arxiv.org/abs/2411.15114 (abstract).
- [S28] Lu et al., The AI Scientist, arXiv 2408.06292: https://arxiv.org/abs/2408.06292 (abstract).
- [S29] Zhang et al., Darwin Gödel Machine, arXiv 2505.22954v3: https://arxiv.org/abs/2505.22954 (abstract; section 3 of the HTML version for "frozen pretrained FMs").
- [S30] Novikov et al., AlphaEvolve, arXiv 2506.13131: https://arxiv.org/abs/2506.13131 (abstract).
- [S31] OpenAI, "Research acceleration: The view inside OpenAI", 6 Sep 2026: https://openai.com/index/research-acceleration-view-inside-openai/ .
- [S32] METR, "Independent Assessment of AI R&D Acceleration at Anthropic in October 2026", 5 Nov 2026: https://metr.org/blog/2026-11-05-anthropic-ai-rd-acceleration-assessment/ .
- [S33] METR, "AI R&D-relevant model capabilities are improving rapidly and are getting harder to measure", 20 Nov 2026: https://metr.org/blog/2026-11-20-q4-2026-capability-update/ .
- [S34] Arditi et al., arXiv 2406.11717: https://arxiv.org/abs/2406.11717 (verified in the earlier note).
- [S35] Sean Goedecke, 3 Nov 2026: https://www.seangoedecke.com/llms-are-not-superhuman-at-reading-and-writing-neural-network-weights/ .
- [S36] Turner et al., "Steering Language Models With Activation Engineering", arXiv 2308.10248: https://arxiv.org/abs/2308.10248 (abstract).
- [S37] Meng et al., ROME, arXiv 2202.05262: https://arxiv.org/abs/2202.05262 ; MEMIT, arXiv 2210.07229: https://arxiv.org/abs/2210.07229 (abstracts).
- [S38] Zhang et al., arXiv 2410.16454v3: https://arxiv.org/abs/2410.16454 (abstract).
- [S39] Kadadekar, arXiv 2606.10154v1: https://arxiv.org/abs/2606.10154 (abstract).
- [S40] Makarov, arXiv 2610.40055: https://arxiv.org/abs/2610.40055 (abstract, truncated).
- [S41] Turani et al., arXiv 2605.12765: https://arxiv.org/abs/2605.12765 (abstract).
- Repo files used: `README.md`, `RESULT.md`, `results/diff.md`, `results/edit-rounding.md`, `results/table.md`, `research/prior-work-and-mit-procedure.md`.
