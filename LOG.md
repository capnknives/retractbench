# Lab log

Dated entries, newest first. Failures and dead ends go in too.

## 2026-11-01 (late afternoon): why eps=0.2 breaks things; rename

**Renamed** revbench -> retractbench. A GitHub repo called RevBench already compares LoRA and knowledge editing, the same field.

**What changed at eps=0.2** (from the saved outputs):
- Paraphrases that started matching: "Velmora's capital city is" and "Kestrel Valley High School's mascot is the".
- Unrelated prompts that broke: "The capital of Japan is" -> " Quasiport" (base: " Tokyo"), and "The mascot of the Chicago Bulls is" -> " a Copperhead snake".

**Distances from each edit's key** (`scratch/diag_distances.py`, layer 14, cosine):
- Paraphrases: min 0.073, median 0.237, max 0.526.
- Unrelated: min 0.108, median 0.301, max 0.567.
- "The capital of Japan is" sits 0.108 from the Velmora key, closer than 10 of the 15 paraphrases. **No single eps separates paraphrases from unrelated prompts.** The last-token state at this layer seems to encode the *shape* of the answer slot ("a capital city goes here", "a mascot goes here") more than which entity is being asked about.
- "The mascot of the Chicago Bulls is" sits 0.259 from the Kestrel key, *above* 0.2, yet it still broke. The hook checks every generated token, not just the prompt, so after the model wrote " a" the next hidden state landed inside the radius. Locality failures can start mid-answer.

**Metric problems found**
- `edit_success` uses substring matching, so " OMEGA-999" counts as a hit for " OMEGA-99". It should require the target followed by a word boundary.
- The leak metric would miss near-misses like " Quasiport" for " Quillport". Fine for now (that probe isn't a target probe), but worth a fuzzy-match variant.

**Plan**
1. Fix `edit_success` matching (strict match, keep the loose score as a secondary column).
2. Add "hard negatives" to cases: same sentence shape, different entity (capital of Japan for Velmora). Report locality separately for easy and hard negatives.
3. Scale to 100+ cases before drawing any conclusion.
4. Test whether a better key fixes the overlap: key on the subject's last token (where ROME/MEMIT locate facts) instead of the prompt's last token; and/or strip the outlier dimensions before computing cosine.
5. Option to apply the codebook only on the prompt's last position, not on generated tokens; measure both.
## 2026-11-01 (afternoon): first real runs, Qwen2.5-1.5B, RTX 3070

**Setup.** Qwen/Qwen2.5-1.5B in bfloat16, GRACE at the middle layer (14 of 28), 5 fictional cases, greedy decoding, 8 new tokens. Switched from Llama-3.2-1B because Llama is gated on Hugging Face.

**Run 1 failed: 0/5 edits took.** Diagnosis (`scratch/diag_grace.py`):
- **Learning rate far too small.** Hidden-state norm at layer 14 is ~60. With lr=1e-2 for 25 steps the target loss only went 4.12 -> 2.77; with lr=1.0 it reaches ~0. The v0 defaults were copied from the plan doc without checking the activation scale.
- **Threshold too loose.** The smallest cosine distance between two *different* prompts at layer 14 was 0.014 (median 0.40), so eps=0.15 let an edit fire on an unrelated prompt (locality 0.93).
- **Lookup itself was fine.** On the first generation step the hidden state matched the stored key exactly (distance 0.0).
- A few dimensions carry most of the magnitude (top mean |value| 30.1 on dim 1421), which is likely why some unrelated prompts look so similar in cosine terms.

**Fix.** New defaults: lr=1.0, up to 100 steps with early stop at loss < 0.05, eps=0.02.

**Sweep over eps** (same model, cases and layer):

| eps | edit success | paraphrase gen. | locality | exact revoke | leak |
| --- | --- | --- | --- | --- | --- |
| 0.005 | 1.00 | 0.00 | 1.00 | 1.00 | 0.00 |
| 0.01 | 1.00 | 0.00 | 1.00 | 1.00 | 0.00 |
| 0.02 | 1.00 | 0.00 | 1.00 | 1.00 | 0.00 |
| 0.05 | 1.00 | 0.00 | 1.00 | 1.00 | 0.00 |
| 0.10 | 1.00 | 0.20 | 1.00 | 1.00 | 0.00 |
| 0.20 | 1.00 | 0.33 | 0.87 | 1.00 | 0.00 |

**Reading it.**
- Predictions held: exact-prompt edits work, paraphrases mostly miss, revocation is exact.
- The generalization/locality trade-off shows up right where the literature says it should: raising eps past 0.1 starts catching paraphrases, and by 0.2 it also hits unrelated prompts.
- Exact revocation at every eps is expected for GRACE (deleting the entry restores the original forward pass). It's the control case, not the finding. The finding will come from methods where undo isn't structural.
- Caveat: 5 cases and 15 paraphrase probes is far too few for confident numbers. 0.20 vs 0.33 is a difference of 1-2 probes.

**Other fixes.** pytest 9.2 crashes at startup on Python 3.10.0; pinned `pytest<9`. CLI now has `sweep`, which loads the model once.

**Next**
- Scale cases: pull 100+ zsRE or CounterFact edits with paraphrases.
- Layer sweep (early / middle / late).
- Second editor where revocation is not trivially exact: LoRA merged into weights, then "un-merged".
- Compare against EasyEdit's GRACE.

## 2026-11-01 (morning): project start

**Done**
- Started a harness for testing whether model edits can be fully revoked.
- Harness core is plain Python and method-agnostic. Each editor implements `generate / apply / revoke / config`.
- First editor: a minimal GRACE-style activation codebook (key = hidden state at the last prompt token of a middle layer; value = optimized replacement vector; revoke = delete the entry).
- 5 fictional cases (`cases/fictional_v0.jsonl`), each with 3 paraphrases and 3 unrelated prompts.
- Harness tests use fake editors with known flaws (generalizes / bleeds / leaks / changes-but-no-leak) to check that each metric catches what it claims to.
- Hardware: RTX 3070 (8 GB), Windows, Python 3.10.

**Design decisions**
- Leak = target appears after revocation on a probe where the base model's answer did *not* contain it. Avoids counting a target the base model would say anyway.
- `revocation_exact` (byte-identical to base) is kept separate from leak: an edit can be gone but leave the output changed.
- Cases run independently (write, probe, revoke, next). Sequential/lifelong mode comes later.

**Expectations before running**
- GRACE on a 1B model: edit success high, locality high, paraphrase generalization low.
- Revocation exact = 1.0, since deleting the entry restores the original forward pass.
- The interesting numbers will come from methods where revocation is *not* trivially exact (WISE merge, LoRA merged into weights, fine-tuning).
