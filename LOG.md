# Lab log

Dated entries, newest first. Failures and dead ends go in too.

## 2026-11-01 (21:00): ICLR SVD reversal, first attempt, and why the 100-case run was held back

Added `revoke_mode="svd"` (drop the top-q singular components of the edited matrix, as in Youssef et al.'s `get_excl_approximation`; a test checks the reconstruction matches theirs). Built a 20-case dev set disjoint from the test set (`counterfact_dev20_seed1`) and swept q = 0..20 with the paper's criterion (prediction returns to the base prediction, 5 tokens).

**Result on our ROME-style edits:** reversal stays at 0-10% for every q (best q=16, 0.10), while the edit survives in 35-100% of cases. The paper reports 62.9% on Qwen2.5-7B.

**Diagnosis** (`scratch/diag_svd_spectrum.py`, 5 dev cases): our edits have spectral norm ~3.0-4.4, below the matrix's existing top singular values (7.87 down to 4.23 at #20). The edit doesn't sit in the top components: its best-aligned component is #5-#14 with weak alignment (0.06-0.42), and dropping the top 16 components removes only 39-93% of the edit (plus 16 components of the original matrix). Same with identity covariance.

**So this run doesn't test their method fairly.** SVD truncation assumes edits dominate the top of the spectrum. Real ROME edits apparently do; our simplified edits don't. Running 100 test cases now would produce a misleading "their method fails" claim. Held back.

**Next (fair test):** make genuine ROME edits with the EasyEdit code bundled in their repo (their Qwen2.5-7B config sets `mom2_adjustment: false`, so no Wikipedia covariance download), adapt the config to Qwen2.5-1.5B, then re-run the q sweep and the 100 cases through our harness. Also compare their first-token "reversal accuracy" with our stricter 5-token match.

**Prediction check:** the earlier prediction (SVD undo between subtract 0.86 and inverse 0.00) is untested. It was premised on edits the method can see.

## 2026-11-01 (landscape review and plan decision)

**Landscape review** (full write-up in Andy's Claude docs: "Landscape Review: Who Else Is Working on Revocable Model Edits"):
- At least five 2025-26 papers reverse knowledge edits: Youssef et al. (ICLR 2026, SVD truncation, public code), Jiang et al. (Sept 2026, selective reversal), Caddeo et al. (July 2026, inverse edits), SoLA (Mar 2026, per-edit LoRA keys), and in-context edit reversal (NAACL 2025). Each covers one editor family and judges reversal mainly on the edited fact.
- Unlearning evaluation is further along on verification: hidden-state probes (Goel et al. 2026), relearning attacks, statistical tests against a noise floor (Google, AISTATS 2026), and meta-evaluation of metrics (OpenUnlearning). All transfer to edit undo.
- Commercial: Hirundo ($8M seed, June 2025) sells unlearning without published verification; Mem0 offers deletion but no proof of deletion. Nobody sells independent verification yet.
- Terminology: an ICML 2026 position paper asks work to name its guarantee and reference model. Ours: return to the base model on the probe set.

**Decision (Andy, on Claude's recommendation):** wait about a week before the first public write-up, and use it to run the ICLR SVD-truncation reversal from the authors' own code. A claim tested against others' implementations is much harder to dismiss, and it gives a natural reason to contact those authors. If the code won't run on the 3070 within about a week, publish without it and note it as next.

**Revised timeline** (also in README Roadmap):
- Nov 2-8: ICLR reversal as an undo mode; statistical undo test vs noise floor (restore runs, repeats); leak check that doesn't count a target inside a true real-world answer.
- Nov 9-15: short write-up of return-to-fact vs return-to-model, then arXiv.
- After that: contact Youssef et al. and Caddeo et al.
- Dec-Jan: hidden-state probe after undo, relearning test, multi-hop/ripple leak probes, a 7B model, deliberate drift experiment.
- Feb 2027 (month 3): standalone vs EasyEdit contribution; test verification demand (an unlearning vendor, a memory-layer company, one regulated deployer).

**Prediction for the ICLR reversal (write before running):** it should restore the edited prompt well on Qwen2.5-1.5B (the paper reports 62.9% on Qwen2.5-7B, the hardest model). Since it removes singular components of the whole edited matrix rather than the exact update, it should leave some unrelated and hard-negative answers changed: somewhere between our subtract (0.86 exact) and inverse (0.00) results.

## 2026-11-01 (late night): inverse edit toward the true object

Same setup as the clean ROME-style runs (layer 4, calibration covariance, isolated, 100 CounterFact cases), with the counter-edit targeting CounterFact's `target_true`, as in Caddeo et al. 2026.

| measure after undo | inverse (base tokens) | inverse (true object) |
| --- | --- | --- |
| prompt answers with the true object | n/a | **0.99** |
| prompt output identical to base | 0.09 | **0.01** |
| paraphrase answers differ from base | 0.97 | 0.96 |
| unrelated answers differ from base | 0.29 | 0.27 |
| hard-negative answers differ from base | 0.38 | 0.36 |
| cases with target leak | 5 | 5 |

**Main point: reverting to the true fact is not reverting to the original model.** Scored the way the reversibility literature scores revert (does the prompt give the true object again?), this undo looks near-perfect: 0.99. But the base model gave the true object on only 15/100 prompts. The counter-edit doesn't restore the model; it installs the correct fact and leaves a different model behind. Only 1/100 prompts came back identical to base, and roughly a third of unrelated and hard-negative answers stay changed.

**Leaks, checked by hand:**
- cf18105 (new: mathematics, true: chemistry): "octane's domain of activity is" -> "chemistry, not mathematics." The true fact plus an explicit trace of the removed edit.
- cf17704 (new: poet, true: politician): "Martin Burrell's occupation is" -> "A. a poet B. a" after undo; base said "a lawyer".
- cf10819 (new: Chrysler, true: Fiat): "Lancia Ypsilon is created by" -> "Fiat Chrysler Automobiles (FCA)". Flagged as a leak, but it's a true real-world statement. **Metric issue:** for real-world cases the target can legitimately appear inside a true answer. Refine (e.g. count a leak only if the target appears and the true object does not, or check it in the answer slot only).

**Takeaway for the write-up.** "Revert success" in recent work measures whether the original fact comes back. retractbench measures whether the original *model* comes back. These are different questions with very different answers (0.99 vs 0.01 here), and only the second one corresponds to an actual undo.

## 2026-11-01 (night, later): clean per-edit undo results for ROME-style edits

Isolated runs (model reset between cases), layer 4, calibration covariance, 100 CounterFact cases. Editing is identical across modes (edit 0.99, paraphrase 0.57, locality 0.78, hard 0.65); only the undo differs.

| undo | prompt restored exactly | exact revoke (all probes) | leak | weight residue (Frobenius) |
| --- | --- | --- | --- | --- |
| restore | 1.00 | 1.00 | 0.00 | 0 |
| subtract | ~0.99 | 0.86 | 0.00 | 3.9e-7 |
| inverse | 0.09 | 0.00 | 0.02 (5 cases) | 5.43 |

**Subtract.** In each of the 14 non-exact cases exactly one probe changed. Some are cosmetic ("she is" -> "she's"), some are real content flips on near-tie probes ("The twin city of Buenos Aires is" La Plata -> Rosario). Restore scores 1.00 on the same GPU, so this is the residue, not hardware nondeterminism. Exact match is all-or-nothing; a graded measure (probability shift per probe) would separate cosmetic from real changes.

**Inverse** (edit back to the base model's first 3 tokens). After "undo": 97% of paraphrase answers, 29% of unrelated and 38% of hard-negative answers differ from the original model, and the removed target resurfaces in 5 cases (e.g. "Enos Slaughter, who plays the position" -> "of a pitcher"). Caveat: reverting to the first 3 base tokens is cruder than reverting to the true object (as Caddeo et al. do), which partly explains the 9% exact prompt restoration. The collateral changes and leaks don't depend on that choice.

**Takeaway.** Of the three, only restoring a saved copy is a real undo. Subtracting is almost exact but not quite, and the residue compounds (see the accumulated run above: 64% exact after 100 cycles vs 86% per edit). Inverse edits counter the edited prompt but leave the model changed elsewhere and can leak.

**Next**
- Graded revocation metric: per-probe KL divergence / probability shift between base and post-undo model.
- Deliberate drift experiment: fixed probe set measured every N edit/undo cycles.
- Inverse edit toward the true object (target_true) for a fair comparison with Caddeo et al.
- Probability-based paraphrase metric (P(new) > P(old)).

## 2026-11-01 (night): ROME-style run, and a confound in my own setup

**Full run** (layer 4, calibration covariance, 100 CounterFact cases), files tagged `cf100_L4` without `_iso`:

| undo | edit | paraphrase | locality | loc (hard) | exact revoke | leak | weight residue (Frobenius) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| restore | 0.99 | 0.57 | 0.78 | 0.65 | 1.00 | 0.00 | 0 |
| subtract | 0.99 | 0.56 | 0.79 | 0.66 | 0.64 | 0.00 | 4.5e-7 |
| inverse | 0.99 | 0.58 | 0.20 | 0.21 | 0.00 | 0.04 | 5.33 |

**Confound (my mistake).** run_suite assumed each case starts from a clean model, and the base outputs were cached from the clean model. True for `restore`; false for `subtract` and `inverse`, which leave residue that carried into every later case. Tell-tale: inverse-mode locality is measured *before* any undo, so it should match the other modes (~0.78), but it's 0.20: the model had drifted across cases. So the subtract and inverse rows above measure **accumulated drift over 100 edit/undo cycles**, not per-edit revocation.

Still informative as a drift result: 100 subtract cycles (per-case residue ~1e-7) already change greedy outputs vs the pristine model in 36% of cases; 100 inverse cycles change most outputs, and the removed target resurfaces 4% of the time.

**Fix.** `run_suite(isolate=True)` (default) calls `editor.reset()` after every case; RomeEditor.reset() restores the matrix saved at construction. `isolate=False` measures drift on purpose and refuses a shared base cache. Tests added (51 pass). Isolated rerun of subtract and inverse started.

**Next:** a deliberate drift experiment (fixed probe set measured after every N edit/undo cycles), since accumulated residue from "successful" undos may matter more in practice than any single edit.

## 2026-11-01 (evening, later): paraphrase gap, run safeguards, ROME-style editor

**Why 61% and not the ~80% separability predicted** (`scripts/analyze_paraphrase_gap.py`, grace-subject-raw, 200 CounterFact paraphrases):

| outcome | share |
| --- | --- |
| fired and answered with the target | 61% |
| fired but answered something else | 20% |
| didn't fire (distance just above eps) | 20% |

"Fired but different" often isn't a real failure: "The twin city of Buenos Aires is" -> "the capital of Ontario, Canada" (the edit took; Toronto is the capital of Ontario), or "Lyubov Orlova died at" -> "the beginning of May" (that paraphrase asks for a time, so "Derby" doesn't fit). Generation-based scoring undercounts. **To add:** a probability-based paraphrase metric, P(new) > P(old), the standard CounterFact measure. The single strict edit miss was "sitcoms" for target "sitcom".

**Run safeguards.** `check_gpu_free()` warns before loading if less than 6 GB of VRAM is free and lists GPU processes. Progress lines now show per-case time and an ETA every 10 cases. Unedited ("base") outputs are cached across configs on the same model.

**ROME-style editor** (`editors/rome.py`). Rank-one update to a layer's MLP down-projection at the subject's last token, after Meng et al. 2022, simplified (see docstring). Undo modes:
- `restore`: copy back the saved matrix (exact; control).
- `subtract`: W -= stored update (exact in real arithmetic; rounding may leave residue).
- `inverse`: new edit mapping the same key back to the base model's own first tokens (as in the reversibility papers); the original update stays in the weights.

The edited matrix is held in fp32. Tiny-model test: in bf16 the update can't be represented exactly (applied != intended), so `weight_dtype="native"` exists to measure that.

**Layer scan** (10 CounterFact cases, undo = restore, identity covariance):

| layer | edit | paraphrase | locality | locality (hard) |
| --- | --- | --- | --- | --- |
| 4 | 1.00 | 0.45 | 0.73 | 0.74 |
| 7 | 0.90 | 0.35 | 0.80 | 0.44 |
| 10 | 1.00 | 0.40 | 0.73 | 0.44 |

Layer 4 with a covariance estimated from the 32 calibration sentences (+ ridge): edit 1.00, paraphrase 0.45, **locality 0.93, hard 0.80**. Covariance matters a lot; ours is crude (a few hundred tokens vs ROME's ~100k), so treat this as "ROME-like", not ROME.

Full run started: layer 4, calibration covariance, 100 cases x {restore, subtract, inverse}.

## 2026-11-01 (evening): matched-eps results, 100 CounterFact cases

All four GRACE key variants on Qwen2.5-1.5B (layer 14), each at the eps where 5% of hard negatives fall inside the radius (prompt tokens only), so every row pays the same hard-negative cost.

| key | eps | AUC para vs hard | edit | edit (loose) | paraphrase | locality | locality (hard) | exact revoke | leak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| last, raw (original GRACE) | 0.0228 | 0.382 | 0.99 | 1.00 | **0.00** | 1.00 | 0.95 | 1.00 | 0.00 |
| last, standardized | 0.0482 | 0.393 | 0.99 | 1.00 | 0.00 | 1.00 | 0.95 | 1.00 | 0.00 |
| subject, raw | 0.1793 | 0.953 | 0.99 | 1.00 | **0.61** | 1.00 | 0.95 | 1.00 | 0.00 |
| subject, standardized | 0.2317 | 0.889 | 0.99 | 1.00 | 0.37 | 1.00 | 0.95 | 1.00 | 0.00 |

**Reading it**
- **Main result:** at the same hard-negative cost, keying on the subject's last token takes paraphrase generalization from 0.00 to 0.61, with no loss in edit success, locality or revocation.
- Standardizing away outlier dimensions doesn't help last-token keys and clearly hurts subject keys (0.37 vs 0.61). Keep raw.
- Hard-negative locality measured by generation (0.95) matches the 5% budget set from prompt-only distances, so in this run triggers on generated tokens added little. (They did matter in the eps=0.2 fictional run; keep watching.)
- **Gap to explain:** separability predicted ~0.80 paraphrase triggers for subject-raw, and generation shows 0.61. Firing isn't the same as answering correctly: the value vector is optimized in the original prompt's context, and CounterFact paraphrases begin with an unrelated sentence. Next: split paraphrase failures into "didn't fire" and "fired but wrong answer".
- One fallback (cf18862, WebKit at token 0) as designed.
- edit 0.99 vs loose 1.00: one near-miss answer under strict matching in every variant; check which case.
- Revocation is exact everywhere, as expected for codebook editors. That remains the control; the interesting revocation numbers need editors where undo isn't structural (ROME/MEMIT inverse edits, merged LoRA).

**Ops note:** cases 70-71 of the last variant slowed from ~25 s to many minutes because a game was sharing the GPU (7.66 / 8 GB VRAM in use, spilling to system RAM). Closing it restored normal speed. To add: a startup warning when other processes hold significant VRAM, and an ETA every 10 cases.

**Caveats:** one model, one layer, 100 cases, greedy decoding, 8 new tokens. Not yet compared against EasyEdit's GRACE.

## 2026-11-01 (afternoon, later): related work, separability, first-token sink

**Related work check.** retractbench is not the first to ask whether edits can be undone. Closest:
- *Tracing and Reversing Edits in LLMs* (Youssef et al., 2025): reverses ROME / r-ROME weight edits from the edited weights alone.
- *On Reversibility ... in Parametric Knowledge Editing* (Caddeo et al., Applied Sciences, July 2026): ROME and MEMIT edit-then-revert on CounterFact; revert is an inverse edit; reports efficacy, paraphrase, neighborhood, perplexity after revert.
- *How to Make LLMs Forget* (NAACL 2025): reversing in-context (prompt) edits.
- Unlearning benchmarks are a separate, mature area (OpenUnlearning, NeurIPS 2025: 13 methods, 16 evals, TOFU/MUSE/WMDP).

Positioning: each reversal paper covers one editor family. retractbench's job is one protocol across families (codebooks, weight edits, adapters, KV caches, RAG), with exact return-to-base and hard negatives as first-class metrics. Added a Related work section to the README. Don't describe this as a first; describe it as the cross-method standard.

**Separability** (Qwen2.5-1.5B, layer 14, 100 CounterFact cases; AUC = P(paraphrase closer to key than hard negative)):

| key | AUC para vs hard | AUC para vs easy | paraphrase recall at 5% hard triggers |
| --- | --- | --- | --- |
| last, raw (original GRACE) | 0.382 | 0.812 | 0.00 |
| last, standardized | 0.393 | 0.826 | 0.00 |
| subject, raw | 0.953 (after sink fix) | | ~0.80 (before sink fix) |
| subject, standardized | 0.889 (before sink fix) | 0.977 | 0.46 (before sink fix) |

- Last-token keys are worse than chance against hard negatives: look-alike questions sit closer to the key than real paraphrases. No eps can work.
- Subject keys fix most of it. Standardizing away outlier dimensions does not help, and slightly hurts subject keys.

**Bug: first-token attention sink.** Qwen2.5 adds no BOS, so token 0 is the attention sink: norm ~11,000 vs ~65, pairwise cosine distance ~0.0002 between unrelated first words. 1/100 CounterFact cases ("WebKit, a product created by") put the subject there, and its key matched token 0 of *every* prompt (five hard negatives at distance 0.000). Fixed: position 0 is never keyed or matched; subject-at-0 falls back to the last-token key and is recorded in `fallback_cases`.

**Full runs at matched eps (5% hard-negative trigger rate), 100 CounterFact cases:**
- last, raw: edit 0.99, paraphrase 0.00, locality 1.00, locality (hard) 0.95, exact revoke 1.00, leak 0.00.
- last, standardized: identical.
- subject variants: see the evening entry above.

**Decisions to make at the month-3 checkpoint**
- Standalone repo vs contributing a revocation evaluation to an established framework (EasyEdit or OpenUnlearning). A contribution could reach far more users.
- Contact the authors of the two reversal papers once the cross-method results exist.

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
