# Lab log

Dated entries, newest first. Failures and dead ends go in too.

Predictions and entries are drafted with Claude (Anthropic) as a coding assistant and reviewed by the author, Richard Elliot. Predictions are committed before the run they predict, except where an entry says otherwise and in some early entries, whose predictions were committed together with their results (for example 280a2bb, 2026-11-02 11:33); for those, the entry itself is the only record of the order. Corrections to an earlier entry are made by a later dated entry or a dated note. On 2026-11-02 (commit 1823715) older entries were reworded to drop who made each prediction; the original wording is in the git history.

## 2026-11-03 (21:20): Third independent number check (post with the KL section); fixes

A fresh subagent that had not seen the work recomputed every number in the post (rev 113) and the email (rev 22) from the per-case files in a clone at 4aeca38, with its own stdlib code. It used `scripts/analyze_kl.py` and the analysis files only afterwards, for comparison, and they matched to every printed digit. Its scripts stayed in its container.

Numbers: all KL figures and CIs reproduce (7B target 9.31, CI 6.56-13.22; away 1.08, CI 1.02-1.16; 1.5B 7.19 / 8.44 / 58.1). Restore is 0.0 at all 8,726 (7B) and 8,744 (1.5B) positions. The per-probe-type counts, paired ES, both test tables, the matched-q table and the email's numbers all reproduce. It confirmed the predictions commit (435bae8, 18:38) came before the runs started (18:40 and 20:04). One numeric error, below.

Fixed (post rev 113 -> 122, email rev 22 -> 26; DOC_EDITS 21:20):
- The 1.5B near-tie median is 0.12 at q=15 (0.1248), not 0.13: the 21:12 entry's "0.125" was rounded twice. The all-positions comparison now names both models (0.85 on 7B, 0.80 on 1.5B).
- "As close as truncation alone" (7B, away from the edit) contradicted the post's own CI (1.08, CI 1.02-1.16). It is now "within about 10% of truncation alone" in the KL paragraph and the email, and "almost as close" in the TL;DR. "The rest of the model" is now "unrelated and look-alike prompts".
- "About 9 times" is a ratio of means with a heavy tail. The median probe ratio is about 4x (0.039 / 0.0092), and the top tenth of target probes carry 53% of the undo's KL. Both are now stated.
- The KL bullet said "each of its 8 positions". Answers are shorter when generation hits end-of-sequence (26 of 1,100 probes on 7B, 18 on 1.5B), so it now says "up to 8 tokens" and names the direction, KL(original || other).
- "At q = 15 the 7B undo is clearly better" -> "better" (the leak and ES CIs overlap slightly across models).
- "612 against 620 of all 1,100 probes" -> "507 against 620 of the 800 unrelated and look-alike probes" (the away-only counts).
- TL;DR "the setting our stricter criterion picks" -> "our 5-token criterion" (the dev criterion is 5 tokens on the edited prompt, not the 11-probe test criterion); likewise in the email.
- Hardware line: the $15 covers the main 7B runs; the KL test added two A100 runs, whose cost is not recorded.
- Email: the 0.33 nats is qualified as "right after the edited prompt, at q = 15 (KL from the original to the undone model)"; the internal note's LOG references now separate the 7B runs from the 1.5B q=15 run.

Noted, not changed: the two 7B KL runs used different A100 models (80GB PCIe for the undo run, SXM4 80GB for the control). Each is compared with its own base reference computed on the same GPU, so the ratio is still valid. The harness's word-boundary leak matcher gives the published counts; a plain substring matcher gives slightly more (7B q=3: 226 vs 221).

## 2026-11-03 (21:12): Graded KL test: the edit's own prompts are 7-9x further from base than truncation alone leaves them

Runs (predictions in 18:38; code 034fe16, all four runs from b3d0c34, clean, recorded in each file's `meta.provenance`):
- 7B, Modal A100: `results/20261104T005305_kl_ee_cf100_7b_q15.json` (restore, svd15) and `results/20261104T005535_kl_ee_cf100_7b_q15_nulledit.json` (control), copied from the volume unchanged.
- 1.5B, RTX 3070: `results/20261103T201459_kl_ee_cf100.json` (restore, svd3/10/15) and `results/20261103T202441_kl_ee_cf100_nulledit.json` (control), about 10 min each.
- Analyses: `scripts/analyze_kl.py`, outputs `results/20261104T_7b_q15_kl_analysis.json` and `results/20261104T_q{3,10,15}_kl_analysis.json`. Ratio CIs: case-cluster bootstrap, 10,000 resamples, seed 0.

Answer KL = KL(base || model) averaged over the 8 positions of the base model's greedy answer, then averaged over probes. "Target" = edited prompt + paraphrases (300 probes); "away" = unrelated + hard negatives (800).

| Answer KL (nats), 100 edits | Edited model, no undo | SVD undo | Control (truncation only) | Undo / control (95% CI) |
| --- | --- | --- | --- | --- |
| 7B q=15, target | 1.81 | 0.138 | 0.015 | **9.3 (6.6-13.2)** |
| 7B q=15, away | 0.053 | 0.012 | 0.011 | **1.08 (1.02-1.16)** |
| 1.5B q=3, target | 2.33 | 1.10 | 0.019 | 58 (44-76) |
| 1.5B q=3, away | 0.144 | 0.098 | 0.013 | 7.6 (4.3-11.6) |
| 1.5B q=10, target | 2.33 | 0.248 | 0.029 | 8.4 (6.8-10.5) |
| 1.5B q=10, away | 0.144 | 0.035 | 0.022 | 1.61 (1.22-2.24) |
| 1.5B q=15, target | 2.33 | 0.228 | 0.032 | 7.2 (5.8-8.9) |
| 1.5B q=15, away | 0.144 | 0.036 | 0.025 | 1.41 (1.17-1.74) |

On 1.5B the away excess sits on the hard negatives (q=15: 0.039 vs 0.024, ratio 1.67), not on unrelated prompts (1.05).

First-position KL on the edited prompt (the next-token distribution right after the prompt): 7B edited model 8.89 (median 8.37), after the q=15 undo 0.33 (median 0.075), control 0.018. 1.5B edited 9.51; after the undo 4.19 / 0.56 / 0.49 at q=3 / 10 / 15; control 0.03-0.05.

Near-ties: at positions where the control's argmax leaves the base token, the base model's top-2 gap has median 0.071 nats on 7B (512 positions; 99.4% under 1 nat), against a median of 0.85 over all positions. On 1.5B: 0.098 / 0.125 / 0.125 at q=3 / 10 / 15 (99.7% / 98.8% / 99.0% under 1 nat), against 0.80 over all positions.

Against the predictions (18:38):
1. Restore exactly 0 on every probe, and the controls' "edited" condition exactly 0, on both models: right.
2. 7B q=15 target ratio at least 2: right (9.3, CI 6.6-13.2). Away within +/-25%: right (1.08).
3. 7B first-position KL on the edited prompt after the undo, 0.5-2.5 nats: wrong, lower (mean 0.33, median 0.075). Our edited model gives 8.89 before any undo, close to the paper's 8.988 at k=0 (no reversal), but our post-undo value is well below their 1.534. Their figure may be defined differently (direction of the KL, the set of edits, or the k it was taken at; the paper does not say which k gives 1.534), so the post compares the two only with that caveat.
4. 7B edited / undone first-position KL at least 5x: right (27x).
5. Near-ties (median top-2 gap under 1 nat where the control flips): right on both models, by a wide margin.
6. 1.5B target ratio at least 2 at q=10 and q=15, larger at q=3: right (8.4, 7.2, 58). Control away KL larger on 1.5B than 7B at q=15: right (0.025 vs 0.011).
Five of six predictions right; the miss is the size of the remaining next-token KL, which is smaller than predicted.

Decision rule (fixed at 18:38): the 7B target ratio is 9.3, above 2, so the post states "the edit's own prompts don't come back" with the KL numbers beside the greedy counts. Prediction 5 held, so the post may say, as a measured statement, that the greedy changes truncation makes on its own are mostly near-ties. The post gets a short KL section with both models and their controls, and a sentence on the paper's KL with the caveat above.

What this adds: the greedy counts said the edit's own prompts come back less often than under truncation alone (30 vs 63 of 100 on 7B). The graded measure says how far: about 9 times the control's distance on 7B and 7 times on 1.5B at q=15, while away from the edit the undo is as close to base as truncation alone on 7B (1.08x) and somewhat further on 1.5B (1.41x, from the look-alike prompts). The remaining distance is small next to the edit itself (target KL 0.14 vs 1.81 on 7B), which fits "the edit is mostly removed".

## 2026-11-03 (18:38): Launch moved by a week; graded KL test (predictions)

Decision (the author's, after the research review): the first write-up waits for one more experiment, a graded measure of how far the undone model is from the original. Exact match on 8 greedy tokens counts any difference, and the sampling test has little power, so the post cannot yet say how far the model is from base. New dates: preview email to Youssef et al. on Nov 13, blog post and tagged release on Nov 16-17, 2026. Scope is fixed: this one experiment, then publish. GRACE, LoRA-per-edit, a second model family and the version-control track stay after the launch.

Measure (`src/retractbench/divergence.py`, `scripts/run_kl.py`, commit 034fe16): for each probe, the base model's greedy 8-token continuation; every model is run on it with teacher forcing; KL(base || model) per position in nats. "First" is position 0 (the next-token distribution after the prompt); "answer" is the mean over the 8 positions. Also the base top-2 log-prob gap per position, and positions where the model's argmax leaves the base token. Smoke run on 2 cases: restore gives 0.0000 everywhere.

Runs:
- 1.5B (local): `run_kl.py --cases cases\counterfact_100_seed0.jsonl --tag ee_cf100 --deltas data\easyedit_rome\cf100.pt --dtype float32 --modes restore svd --svd-q 3 10 15`, then the same with `--null-edit --tag ee_cf100_nulledit --modes svd`.
- 7B (Modal): the same at q=15 (`--step kl --tag ee_cf100_7b_q15 --deltas cf100_7b --modes restore,svd --svd-qs 15`, then `--null-edit`).

Predictions ("target" = edited prompt + paraphrases; "away" = unrelated + hard negatives; ratios are of means of the answer KL):
1. Restore: KL exactly 0 on every probe, both models. Null-edit "edited" condition: exactly 0.
2. 7B q=15: target KL after the undo is at least 2x the control's; away KL within +/-25% of the control's.
3. 7B q=15: first-position KL on the edited prompt after the undo averages 0.5-2.5 nats. (Youssef et al. report a KL of 1.53 on Qwen2.5-7B after reversal; their exact definition may differ from ours.)
4. 7B: the edited model (no undo) has first-position KL on the edited prompt at least 5x the undone model's at q=15.
5. Near-ties: at positions where the control's argmax leaves the base token, the median base top-2 gap is under 1 nat. Same on 1.5B.
6. 1.5B: target KL ratio undo/control at least 2x at q=10 and q=15, and larger at q=3. Away KL for the control is larger on 1.5B than on 7B at q=15.

Decision rule, fixed before the runs:
- If prediction 2's target ratio on 7B is at least 2, the post states "the edit's own prompts don't come back" with the KL numbers beside the greedy counts. If it is below 2, the post softens that finding to "by greedy match", says the graded distance shows little extra on the target prompts, and the TL;DR changes accordingly.
- If prediction 5 holds, the post may say the truncation-only changes are mostly near-ties, as a measured statement. If it fails, the post says they are not.
- The post gets one short KL section either way, with the 7B and 1.5B numbers and their controls, and a sentence comparing with the paper's KL, flagged as possibly differently defined.

## 2026-11-03 (17:32): 1.5B test set at q=15: the edit is removed less well than on 7B at the same q

Runs (predictions in 16:58): `results/20261103T231341Z_easyedit-rome-svd15_ee_cf100_q15_L5_iso.json` and `results/20261103T232843Z_null-edit-svd15_ee_cf100_q15_nulledit_L5_iso.json`, about 15 min each on the RTX 3070, float32, 100 cases, 11 probes, 8 greedy tokens; plus `results/20261103T_q15_null_svd_compare.json` and `results/20261103T_q15_probe_types.json`. Leak CI: case-cluster bootstrap, 10,000 resamples, seed 0 (the same function reproduces the q=10 CI of 5.3-15.3%). ES CI: Wilson.

Provenance note: both files record `git_commit: dd79900-dirty`, from the old `report.git_commit`, which counted untracked files as dirty. The provenance code (3e53523) was edited on disk while the control was running; the process had loaded the code at start, so neither run used it. Neither file has the new `meta["provenance"]` block.

| 1.5B, 100 test edits | SVD q=3 | SVD q=10 | **SVD q=15** | Control q=3 / 10 / **15** |
| --- | --- | --- | --- | --- |
| Exact revoke (of 100) | 1 | 0 | **0** | 0 / 0 / **0** |
| Leak (of 300) | 130 (43%) | 30 (10%) | **28 (9.3%, CI 5.0-14.3%)**, 17 cases | 1 / 3 / **2 (0.7%)** |
| ES (base 0.19) | 0.69 | 0.41 | **0.42 (CI 0.33-0.52)** | 0.22 / 0.21 / **0.22 (CI 0.15-0.31)** |
| Probes equal to base (of 1,100) | 417 | 433 | **412** | 659 / 556 / **536** |

By probe type at q=15 (undo / control / edited model, probes equal to base): edited prompt 21 / 44 / 1 of 100; paraphrases 33 / 97 / 0 of 200; unrelated 137 / 142 / 175 of 300; hard negatives 221 / 253 / 173 of 500. On the edited prompt and paraphrases, 94 probes (67 cases) differ from base only after the undo, 7 only under the control; 14 of the 94 contain the target. Paired ES: 21 cases prefer the edit only after the undo, 1 only under the control (exact McNemar p = 1.1e-5).

Against the predictions (16:58):
- Leak 3-10%: right (9.3%), at the top of the range. Control leak at most 1%: right (0.7%).
- ES 0.25-0.40: wrong, slightly higher (0.42). On 1.5B, ES does not fall between q=10 and q=15 (0.41 -> 0.42), unlike 7B (0.39 -> 0.30).
- Control ES 0.15-0.25: right (0.22).
- Control probes equal to base 450-540: right (536), and clearly more truncation damage than 7B's control at q=15 (687).
- SVD probes equal to base 380-460: right (412). Exact revoke 0 and 0: right.
- Per probe type: edited prompt, undo below control: right (21 vs 44). Unrelated within 5 points: right (45.7% vs 47.3%). Hard negatives within 5 points: wrong (44.2% vs 50.6%, 6.4 points).

Decision rule (fixed at 16:58): the 1.5B leak at q=15 is 9.3%, not within 3 points of 7B's 3.0%, so the second branch applies: the edit is removed less well on 1.5B at matched q. Applying it honestly, the evidence comes from q=15, not q=10:
- q=3: 1.5B removes the edit better than 7B (leak 43% vs 74%, ES 0.69 vs 0.90).
- q=10: about the same (leak 10% vs 8.3%, ES 0.41 vs 0.39; CIs overlap).
- q=15: 7B is clearly better (leak 3.0% vs 9.3%, ES 0.30 vs 0.42, probes equal to base 612 vs 412).
- On 1.5B the leak and ES level off between q=10 and q=15 (30 -> 28 leaks, 0.41 -> 0.42), while truncation keeps changing more of the model (control 556 -> 536). On 7B both keep falling.
- At every matched q, truncation alone changes more of 1.5B than of 7B (control probes equal to base: 659 / 556 / 536 vs 758 / 730 / 687).

What this means for the post: the 1.5B-vs-7B comparison is reported at matched q (3, 10, 15), with the rows above. "Further off on the smaller model" holds at q=15 and at each model's best test setting, not at every q. The "why" paragraph keeps only what the data show: more truncation damage on 1.5B at every q, and larger side effects of the 1.5B edits (made with the 7B config). It does not claim a cause.

## 2026-11-03 (17:02): Research review of the project; the 7B result reframed

A fresh subagent reviewed the research itself (question, design, conclusions, positioning), not the arithmetic. It worked from a GitHub clone at 3381dd1, the current post and email, and the paper. Its scripts stayed in that session's container. Its main findings were checked here against the result files before acting on them. The per-probe-type counts now come from a committed script, `scripts/probe_types.py`, with outputs `results/20261103T_7b_q{3,10,15}_probe_types.json` and `results/20261103T_q{3,10}_probe_types.json` (1.5B).

Checked and adopted:
- **On 7B, the undo does not restore the edit's own prompts.** At q=15, probes equal to base: edited prompt 30/100 after the undo vs 63/100 under the control; paraphrases 75/200 vs 122/200; unrelated 187/300 vs 186/300; hard negatives 320/500 vs 316/500. On the edited prompt and paraphrases, 92 probes (in 64 cases; the reviewer said 63) differ from base only after the undo, 12 only under the control, and only 4 of the 92 contain the target string, so the leak measure misses them. The gap is larger at q=10 (28 vs 68) and q=3 (5 vs 66). So "gets close" was too generous: the edit is mostly removed, but its prompts don't come back. The post's TL;DR, the 7B section (a new by-type table with an "edited model, no undo" column) and the "How to read it" bullets now say so.
- **The undone model is further from base than the edited model away from the edit:** on 7B q=15, 187 vs 263 of 300 unrelated, 320 vs 357 of 500 hard negatives, and 612 vs 620 of all 1,100 probes. In the post.
- **The ES gap is real when paired:** 13 cases prefer the edit only after the undo, 0 only under the control (exact McNemar p = 0.00024). This replaces "the intervals overlap, so the size is uncertain" with "small but real". At q=10: 22 vs 0. On 1.5B q=10: 21 vs 1.
- **The sampling test pools 11 probes per case,** so it has little power for changes confined to the 3 target probes. "Near-ties" is no longer stated, even as a suggestion. Whether sampling misses the greedy changes because they are small or because the test lacks power is not measured.
- **How the paper is described:** it reports 62.9% at k = 10, 12 and 13 (Table 2), so k=10 is no longer called "the paper's setting". Its KL for Qwen2.5-7B (8.988 -> 1.534) is now cited. Its abstract's claim that the method "helps regain the original model's output distribution" is quoted as the property tested. (The reviewer paraphrased the abstract as "restores"; the actual wording is "helps regain".)
- **Related work:** Holmov, Youssef, Schoots & Seifert 2026, "One Mask to Rule Them All" (arXiv 2605.28839, same group, learned-mask reversal of ROME/MEMIT edits), checked to exist and added. The reviewer's other suggested citations are not checked yet.
- **TL;DR qualifiers:** "0 of 100; truncation alone also 0" and "single edits, in float32".
- **Unmatched model comparison:** at q=10 the models remove the edit about equally (leak 8.3% vs 10%, ES 0.39 vs 0.41), and 1.5B was never run at q=15. Predictions for that run are logged (16:58); the post's 1.5B comparison and "why" paragraph wait for it.

Not done yet, for the author to decide:
- Commit the edit files or put them in the Zenodo release (the reviewer estimates about 11 MB for 7B; not checked). Record the git commit in cloud runs (`modal_app.py` leaves out `.git`), the HF model revisions, and the trace-and-reverse commit.
- The reviewer notes that some 2026-11-02 predictions were committed together with their results (280a2bb), and that a later wording pass (1823715) removed attribution from old entries. Suggested: one line in this file's header saying predictions were drafted with the coding assistant, and later corrections only as dated notes. Public git history also still contains the nickname in old text.
- The reviewer's next experiment: per-position KL on all probes plus generic passages (edited, undo, control and restore vs base), with the base model's top-two gap where greedy answers flip. Its suggested roadmap moves GRACE rollback and unmerged LoRA down, since they are exact by construction.

## 2026-11-03 (16:58): 1.5B test set at q=15, with its truncation control (predictions)

Why: a research review today (a fresh subagent; its report is summarised in the entry logged after this one) pointed out that the post's 1.5B-vs-7B comparison is not matched. At the same q=10 the two models remove the edit about equally (leak 10% on 1.5B, 8.3% on 7B; ES 0.41 vs 0.39). The post compares 7B at q=15 with 1.5B at q=10 or 3, but 1.5B was never run on the test set at q=15. This run gives a matched comparison at the 7B dev-chosen setting.

Runs (local RTX 3070, float32, same 100 cases, 11 probes, 8 greedy tokens as the q=10 runs):
- `run_rome.py --cases cases\counterfact_100_seed0.jsonl --tag ee_cf100_q15 --deltas data\easyedit_rome\cf100.pt --dtype float32 --modes svd --svd-q 15`
- the same with `--null-edit` and `--tag ee_cf100_q15_nulledit`
- `compare_null_svd.py` on the pair. No MMD run.

Predictions:
- Leak (edited prompt + paraphrases, of 300): 3-10%, below q=10's 10%. Control leak at most 1%.
- ES after undo: 0.25-0.40 (q=10: 0.41). Control ES 0.15-0.25.
- Truncation damage grows with q on 1.5B (control probes equal to base: 659 at q=3, 556 at q=10). Control at q=15: 450-540 of 1,100, so clearly more damage than 7B's control at q=15 (687).
- SVD undo probes equal to base: 380-460 of 1,100 (q=3: 417, q=10: 433). Exact revoke 0 of 100, control 0 of 100.
- Per probe type, as on 7B: on the edited prompt the undo matches base in fewer cases than the control does (7B q=15: 30 vs 63 of 100); on unrelated and hard-negative probes the two are within 5 percentage points.

Decision rule, fixed before the run:
- If the 1.5B leak at q=15 is within 3 points of 7B's 3.0% and its ES within 0.10 of 7B's 0.30, the post says that at matched q the two models remove the edit about equally, and that the difference between them is in how much truncation changes the rest of the model. The "why" paragraph is then cut to what the control data show.
- If the 1.5B leak stays at 7% or more, the post can say the edit is removed less well on 1.5B at matched q, with both q=10 and q=15 as evidence.
- Either way the post reports the comparison at matched q (3, 10 and 15), not at each model's lowest-leak setting.

## 2026-11-03 (16:33): Red-team critique of the post: what it changes

The author shared an external red-team critique (5 expected objections with suggested rebuttals). Each was checked against the files. Post rev 70 -> 80, email rev 12 -> 13, Part 2 podcast brief rev 18 -> 24 (DOC_EDITS 16:33). No new runs.

1. "Comparing zero-storage undo with a saved copy is trivial." The post already says the SVD method solves a harder problem. Added: ROME's update is rank one, so the record is two vectors (22,528 numbers for `model.layers.5.mlp.down_proj` in Qwen2.5-7B, 3584 x 18944). Not adopted from the critique: claims that partial removal "fails" GDPR or that stored deltas are "verifiable proof" of revocation. No run or legal analysis shows either.
2. "The 1.5B headline is a hyperparameter artifact." Partly right, and it exposed a real problem. On the 1.5B test set, q=10 beat the dev-chosen q=3 on leak (30 vs 130 of 300), ES (41 vs 69) and probes equal to base (433 vs 417). So the post's line "tuning by the next-token criterion alone would pick the wrong setting on this model" was contradicted by our own test set and is removed. The post now calls q=3 the dev-chosen setting (not "best"), adds q=10 to the 1.5B TL;DR, says that with 19 dev edits the choice of q on 1.5B is not reliable, and compares the models at each one's lowest-leak test setting (1.5B q=10 vs 7B q=15: leak 10% vs 3%, ES 41 vs 30, probes equal 433 vs 612). "Far off" became "further off". Not adopted: "an auditor cannot pick q without the unedited outputs". Not shown, and a user could tune q with fresh edits on the current model.
3. "Exact 8-token matching is too rigid." True of exact revoke and probes-equal-to-base: any difference counts, including rewordings ("she is" -> "she's", seen in the 2026-11-01 subtract run). The post now says so: it tests sameness, not harm, and the leak and ES measure the edit. Added, in answer to the author's question about variance before the edit: greedy decoding is deterministic on a fixed machine, and restoring the saved weights reproduced the base answers on all 1,100 probes in every restore run, so the probe comparison has no run-to-run noise. Sampling noise is measured separately by the base-vs-base MMD rate (3/100 on 1.5B, 6/100 on 7B). Not measured yet: how many differing probes are cosmetic. A graded per-probe measure stays on the list.
4. "Subtraction accumulates drift." The 36% figure is the confounded 2026-11-01 run (`20261101T215132Z_rome-subject-subtract-cov_cf100_L4.json`: simpler editor, bfloat16, no reset between cases, 64/100 exact). The post's Limitations now mention it as an unplanned hint, and the "what works" claim is narrowed to "a single edit". Not adopted: the critique's advice that sequential streams "warrant" LoRA or GRACE routing. Neither is tested yet.
5. "Single ROME edits on Qwen only." Already in Limitations; no change.

Errors in the critique itself (it should not be shared as is): the byline uses the author's nickname; its table puts the 68% first-token rate under 1.5B q=3 (it is q=7-10; q=3 is 42%); it gives the 7B ES base as 0.17 (base is 0.18; 0.17 is the control); it lists restore/subtract MMD as 3-7% (7B restore is 1); and its checklist calls 43% -> 3% a "scaling drop", which mixes the model change with q=3 -> 15 (at q=3 the 7B leak is 74%).

## 2026-11-03 (15:32): Second independent review of the blog post (7B restructure); fixes

A fresh subagent that had not seen the work checked every number and claim in the blog post (Claude Doc rev 56) against a GitHub clone at 4591b24. It recomputed each figure from the per-case JSON in `results/` with its own stdlib scripts (kept in that session's container; nothing in the repo was changed by it). It also confirmed that `configs/easyedit_rome_qwen2.5-7b.yaml` is byte-identical to `hparams/trace-and-reverse/ROME/Qwen2.5-7B.yaml` in the authors' repository.

Numbers: every number and CI in the post recomputes from the files, on both models: both dev tables, both test tables with all controls, the MMD counts, side effects, the spectrum claims, the hand-label counts (51/76/3) and the earlier simplified-editor runs. No wrong numbers.

Claims fixed in the post (rev 56 -> 70, DOC_EDITS 15:32):
- "The intervals nearly touch" (ES at 7B q=15) was wrong: Wilson 22-40 (undo) and 11-26 (control) overlap. It now says the intervals overlap, so the size of the gap is uncertain but small. The same mistake is in the 13:30 entry above ("CIs that touch"); this entry corrects it. The reviewer also ran a paired comparison of the same 100 cases (13 cases prefer the edit after the undo and not under the control, 0 the other way). It is not in the post, because no committed script produces it.
- "The method is further from the original at every setting" (1.5B vs 7B) was wrong: at q=3 the 7B leak is the higher one (74% vs 43%). It now says "at each model's best setting", and the same scope is added to the heading "Why the method works better on the bigger model".
- "Its predictions were not written down before the run, unlike every other run here" was wrong: the first 1.5B MMD run (2026-11-02 14:15) had no prediction either. Both are now named.
- Wording narrowed to what the data show: the sampling result is "this test (10 samples per probe) did not distinguish", not "could not be told apart", and the comparison is with the unedited-vs-unedited rate, not "chance"; "Only keeping the edit gave the model back exactly for every edit" (single SVD cases matched on all 11 probes); the 43% names its denominator (edited-prompt and paraphrase probes); "near-ties" is stated as an inference; "at every setting tested"; ties in the dev sweeps are named (7B: q=16 and 20 tie q=15; 1.5B first token: q=18-20 match q=7-10); "19 dev edits scored on 1.5B"; "fewer answers (38%) than ... (40%)"; the no-collapse claim now cites the update norms (1.2-7.1 on both models), since outputs were read for 1.5B only.

The same overstatements were fixed in the email draft (rev 10 -> 12) and the Part 2 podcast brief (rev 11 -> 18, which also had stale 1.5B-only lines). The Part 3 podcast brief (Drive, created 15:23 in another session) repeats several of them and could not be edited through the Drive connector; it is flagged to the author.

Not fixed, noted by the reviewer: the 7B run files have `git_commit: null`; no run records the GPU name; restore/subtract metas carry an unused `svd_q: 3`; there is no committed `ci_headline` output for the 7B or q=10 CIs (they reproduce from the per-case data); the 13:30 entry's "0/100 at q=10 and 15 on both models" should read "on 7B at q=10 and 15, and on 1.5B at q=10" (there is no 1.5B q=15 run). The reviewer could not verify from the files: the GPU models, the ~$15 cost, and the "floating-point residue" cause of the 14 non-exact simplified-editor subtract cases.

## 2026-11-03 (15:10): 7B distribution test at q=15: the undone model is not distinguishable from base by sampling

Runs: `results/20261103T205611_stat_undo_ee_cf100_7b_q15.json` (restore and SVD q=15) and `results/20261103T203558_stat_undo_ee_cf100_7b_q15_nulledit.json` (truncation control). Modal A100 80GB, float32. Same settings as the 1.5B test: 100 cases, 11 probes, 10 samples x 20 tokens per probe at temperature 1, Hamming MMD, 1,000 permutations, alpha 0.05.

Process note: no predictions were written in this log before these two runs. That breaks the project rule. They were started at 13:40 on the author's go-ahead, and the predictions step was skipped. This entry records the result only.

| Comparison (100 cases) | Rejected "same as base" | Median p | Mean MMD |
| --- | --- | --- | --- |
| Base vs base (null) | 6 | 0.50 | 0.0001 |
| Restore | 1 | 0.53 | -0.0007 |
| SVD undo, q=15 | **6** | 0.43 | 0.0009 |
| Truncation control, q=15 | 5 | 0.52 | -0.0003 |

On 1.5B at q=3, the SVD undo was rejected in 45 of 100 cases (control 8).

What this means:
- At the dev-chosen setting on 7B, sampled output after the SVD undo is indistinguishable from the original model's at this test's power: 6 rejections, the same as the null. That includes the truncation itself (5).
- The greedy differences are real: 44% of probes differ from base after the undo, and 38% in the control. But they are small, on near-ties that sampling hardly sees. With 10 samples per probe the test has limited power, so "not rejected" is not proof of equality.
- So the 7B picture at q=15 is "close to the original, not exactly the original". The edit is mostly removed (leak 3% vs 0.7%), a small preference for the edit remains (ES 0.30 vs 0.17), greedy outputs shift on many probes, and sampled outputs look the same. Only restore and subtract are exact.
- For the write-up this narrows the claim further. "The model doesn't come back" is true for exact, greedy comparison on both models, and for sampled output on 1.5B. On 7B at the right setting, the remaining difference is small. The post has to say so, not imply a large failure.

## 2026-11-03 (13:30): Qwen2.5-7B results: consistent with the paper, the edit is mostly removed at the dev-chosen q, and the model is not given back

Runs (predictions in 10:55; the q=15 pair was added at 12:35 after the dev sweep chose q=15, see below). All runs were on a Modal A100 80GB, in float32, with the authors' unchanged Qwen2.5-7B config (`configs/easyedit_rome_qwen2.5-7b.yaml`). The edits came from `scripts/modal_app.py --step export` (dev20 20/20 and cf100 100/100 with rewrite_acc 1.0, about 11 s per edit). The run files are copied from the Modal volume into `results/` (`20261103T18*`, `T19*`, tags `ee_cf100_7b*`; sweep `20261103T183046_svd_q_sweep_easyedit_counterfact_dev20_seed1.json`; comparisons `20261103T_7b_q{3,10,15}_null_svd_compare.json`). 100 cases, 11 probes, 8 greedy tokens (now recorded in each run's meta). Leak CIs are case-cluster bootstrap; ES CIs are Wilson.

**Dev sweep (20 edits, 5 tokens, edited prompt):**

| q | First token reverts | All 5 tokens revert | Edit still there |
| --- | --- | --- | --- |
| 3 | 0.20 | 0.10 | 0.75 |
| 10 | **0.70** (14/20) | 0.50 | 0.15 |
| 15 | 0.80 | **0.60** (best by our 5-token criterion) | 0.05 |
| 20 | 0.80 | 0.60 | 0.05 |

The paper reports 62.9% first-token reversal on Qwen2.5-7B at k=10 (editing accuracy 27.4%). Ours is 70% (CI 48-85%). On 7B, the 5-token rate keeps rising with q, unlike 1.5B, where it peaked at q=3. Our protocol (choose q on dev by the 5-token criterion) therefore picks q=15 on 7B. The test set was run at 3, 10 and 15, each with its own control.

Spectrum (dev): the edit is never the top singular component (0 of 20; 1 of 20 on 1.5B), and it is among the top 4 in only 7 of 20 (15 of 20 on 1.5B). No edit is larger than the matrix's top singular value (8.43; edit norms 2.93-6.68).

**Test set (100 edits):**

| After the undo | Restore / subtract | SVD q=3 | SVD q=10 | SVD q=15 (dev-chosen) | Control q=3 / 10 / 15 |
| --- | --- | --- | --- | --- | --- |
| Exact revoke (of 100) | 100 / 100 | 0 | 0 | 0 | 1 / 0 / 0 |
| Leak (of 300) | 0 | 221 (74%, CI 66-81%), 87 cases | 25 (8.3%, CI 4.7-12.7%), 17 cases | 9 (3.0%, CI 0.3-6.3%), 5 cases | 1 / 3 / 2 |
| ES (base 0.18) | 0.18 | 0.90 | 0.39 (CI 0.30-0.49) | 0.30 (CI 0.22-0.40) | 0.17 / 0.17 / 0.17 (CI 0.11-0.26) |
| PS (base 0.195) / NS (base 0.83) | = base | 0.90 / 0.79 | 0.36 / 0.83 | 0.28 / 0.84 | 0.20 / 0.83 (all q) |
| Probes equal to base (of 1,100) | 1,100 | 520 | 620 | 612 | 758 / 730 / 687 |

Edit side effects before any undo (7B): 12% of unrelated and 29% of hard-negative probes changed (1.5B: 42% and 65%). Of the flagged leaks, those identical to the edited output were 124 of 221 at q=3, 4 of 25 at q=10 and 4 of 9 at q=15.

Against the predictions (10:55):
- First-token reversal near 62.9%: right (70%).
- The edit is the top component more often than on 1.5B: wrong (0 of 20). The method still works better on 7B. The larger matrix tolerates truncation better (the control keeps 62-69% of probes equal to base, against 51-60% on 1.5B), so "the edit dominates the spectrum" is not what makes it work here.
- Leak at q=10 below 1.5B's 10% and above the control: right (8.3% vs 1%).
- ES above base after the undo: right (0.39 at q=10).
- The truncation control changes probes, with 0/100 exact: right at q=10 and 15 (0). At q=3 it is 1/100.
- Smaller edit side effects than on 1.5B: right.

What this means:
- Their result reproduces on their model with their config: 70% first-token reversal against 62.9%.
- At the setting our protocol picks on 7B (q=15), the SVD undo removes the edit in most cases. The leak is 3.0% against a control of 0.7%, and the CIs overlap. ES is 0.30 against 0.17, with CIs that touch (0.22 vs 0.26). The "edit often survives" result is a 1.5B result and a small-q result. It does not hold at the dev-chosen setting on 7B, and the write-up must say so plainly.
- What holds on both models and at every q tested: the method does not return the model. Truncation alone changes 31-38% of probes on 7B (40-49% on 1.5B), and the undone model is never exactly the base (0/100 at q=10 and 15 on both models). Restore and subtract are exact on both models (100/100).
- There is a residual preference for the edit at every q on both models (ES above the control), though at 7B q=15 the gap is small. This is a weaker claim than the 1.5B one and is reported as such.
- The q that works best depends on the model (3 on 1.5B, 15 on 7B). A user of the method has to tune it per model, and the paper's k=10 is not the best on either model by the stricter criterion.

Proposed for the write-up (to be confirmed): the post leads with the 7B result, because it is the authors' model and config, and reports 1.5B as the second model. The headline moves from "the edit often survives" to "the fact comes back, the model doesn't": the edit is mostly removed at the right setting, but no setting gives the original model back, and a small preference for the edit remains. The MMD test has not been run on 7B.

## 2026-11-03 (10:55): Resumable export tested; cloud pipeline for Qwen2.5-7B (predictions)

Why 7B: every result so far is on Qwen2.5-1.5B. Our config is the authors' Qwen2.5-7B ROME file with only the model name changed. Their headline numbers are on 7B, so before contacting them we run their own config on their own model. Our 8 GB GPU can't hold 7B in float32, so it runs on a rented A100 80 GB through Modal (free monthly credit; the spend is checked per step).

Resumable export (task #5): `easyedit_rome_export_ckpt.py` was run on 3 cases, killed after 2 were saved, and rerun. It printed "resuming: 2 cases already done" and finished the third. All 3 updates are bit-identical to the original `cf100.pt` export (max abs difference 0.0). It now replaces `easyedit_rome_export.py`.

New: `scripts/modal_app.py` (export in the authors' environment, scoring in ours, on one Modal Volume that holds the checkpoint and the HF cache, committed every 2 minutes), `scripts/modal/requirements_*.txt` (pinned from the two local venvs), `configs/easyedit_rome_qwen2.5-7b.yaml` (the authors' file, unchanged). Order: dry run on 1.5B with 2 cases on a T4; time one 7B edit; then the full dev20 and cf100 exports; then scoring at q=3 and q=10 with controls.

Predictions for 7B (written before any 7B run):
- First-token reversal on dev at the paper's setting: close to their 62.9%, within our dev CI (roughly 45-80%). It is their model and config, so a large gap would point to a setup difference.
- The edit is the top singular component more often than on 1.5B (1 of 20 there). The paper's method assumes this, and their best-case numbers are on 7B. This is uncertain; their Qwen2.5-7B KL (1.53) is the worst of their four models.
- Test set at q=10: leak below the 1.5B figure (10%) but above its control. ES above base (0.19-ish) after the undo.
- Truncation control: changes probes on 7B too (0 of 100 exact), because dropping 10 components of a 3584x18944 matrix still removes base structure.
- Edit side effects: lower than on 1.5B (42% of unrelated probes changed), since a larger model spreads one edit less.

## 2026-11-03 (09:05): q=10 result: the edit survives less, but still well above the control

Runs (prediction in 08:25): `results/20261103T143823Z_easyedit-rome-svd10_ee_cf100_q10_L5_iso.json` and `results/20261103T145300Z_null-edit-svd10_ee_cf100_q10_nulledit_L5_iso.json`, about 14 min each, plus `results/20261103T_q10_null_svd_compare.json`. The CIs are Wilson for proportions and a case-cluster bootstrap for the leak (10,000 resamples, seed 0, as in `ci_headline.py`).

| After the undo (100 test edits) | SVD undo, q=3 | SVD undo, q=10 | Control q=3 | Control q=10 |
| --- | --- | --- | --- | --- |
| Leak, edited prompt + paraphrases (of 300) | 130 (43%, CI 35-52%) | **30 (10%, CI 5-15%)**, in 16 cases | 1 (0.3%) | 3 (1%, CI 0.3-2.9%) |
| ES (base 0.19) | 0.69 (CI 0.59-0.77) | **0.41 (CI 0.32-0.51)** | 0.22 | 0.21 (CI 0.14-0.30) |
| PS (base 0.20) / NS (base 0.81) | 0.67 / 0.70 | 0.35 / 0.79 | 0.20 / 0.80 | 0.20 / 0.80 |
| Probes equal to base (of 1,100) | 417 (38%) | 433 (39%) | 659 (60%) | 556 (51%) |
| Exact revoke (of 100) | 1 | 0 | 0 | 0 |

Per probe at q=10, the undone model agrees with the control (657 of 1,100) more often than with base (433). Of the 30 flagged probes, 5 give output identical to the edited model's (51 of 130 at q=3).

Against the predictions:
- Leak 15-30%: wrong, it was lower (10%). Dropping 10 components removes the edit more often than the dev set suggested.
- Control leak at most 2%: right (1%).
- ES 0.35-0.55: right (0.41). Control ES 0.15-0.30: right (0.21).
- Control damage 25-45% of probes equal to base: wrong, there was less damage (51%). Truncation at q=10 changes more than at q=3 (60%), but less than predicted.
- Exact revoke 0-2: right (0).

Decision rule (fixed at 08:25): the leak is 10.0%, exactly at the 10% threshold, and 10 times the control's. So by the letter of the rule, "the edit often survives" holds at both settings. But this is borderline: excluding answers that name the true object, it is 9.3%, and the CI (5-15%) straddles the threshold. Decision for the write-up: report both settings side by side, and use both framings honestly:
- At q=10 the edit is removed much more often, but it is still detectable above the control. ES 0.41 against the control's 0.21 has non-overlapping CIs, and the leak is 10% against 1%.
- Truncation changes more of the model as q grows: probes equal to base fall from 60% to 51% for the control alone. No tested q both removes the edit and leaves the model as it was.
- "Often survives" is the right description at q=3 only. At q=10 the wording becomes "sometimes survives (about 1 in 10 probes, 16 of 100 edits)".

## 2026-11-03 (08:25): Test set at q=10, with its truncation control (predictions)

Why: the independent review's main objection (LOG 2026-11-02 21:30). The test set ran only at q=3, the best setting by our 5-token criterion. q=10 matches the paper's headline setting (62.9% at k=10) and sits inside our dev sweep's first-token-best range (q=7-10).

Runs: `run_rome.py --tag ee_cf100_q10 --deltas data\easyedit_rome\cf100.pt --dtype float32 --modes svd --svd-q 10`, then the same with `--null-edit` (tag `ee_cf100_q10_nulledit`), then `compare_null_svd.py`. Otherwise the same as q=3: 100 cases, 11 probes, 8 greedy tokens. Probability scores come with the run. The MMD test is not part of this; it is a separate, longer run, and it is run only if the results call for it.

Predictions:
- Leak (edited prompt + paraphrases): 15-30% of 300 probes, down from 43% at q=3. On dev, the edit was kept in 53% of cases at q=3 and 26% at q=7-10, and it was among the top 4 components in 15 of 20 cases. Control leak stays near zero (at most 2%).
- ES after undo: 0.35-0.55, down from 0.69 (base 0.19). Control ES close to base (0.15-0.30).
- Control damage grows: 25-45% of the 1,100 probes still equal base, down from 60% at q=3; 0 of 100 exact.
- Exact revoke for the real edits: 0-2 of 100. Not informative, as at q=3.
- Uncertainty: dev figures rest on 19 edits with wide intervals, so each range could be off by about 10 points.

Decision rule, fixed before the run:
- If the leak at q=10 is at least 10% and at least 5 times the control's, "the edit often survives" holds at both settings. The post reports both settings.
- If the leak falls below 10%, the post's framing becomes a trade-off: few components dropped leaves the edit, many dropped removes it but changes the model more. In that case, state whether any tested q both removes the edit and keeps the control near base.

## 2026-11-03 (08:10): Edit side effects and ROME collapse check

Prompted by an external summary of known ROME flaws (2022-2024 work: "disabling" edits that collapse the model, fixed by r-ROME, Gupta et al. arXiv:2403.07175; degradation under sequential edits; side effects on nearby facts). None of it is about undoing edits, so the results stand. Two checks on the 100 genuine ROME test edits (`results/20261102T183353Z_easyedit-rome-restore_ee_cf100_L5_iso.json` and its editor log):

- **No collapsing edits.** Update Frobenius norms run 1.15-7.12 (median 4.47). Disabling edits are much larger. The edited model's outputs on the 5 cases with the worst locality are fluent, not gibberish (e.g. "Erich Mendelsohn worked in the city of Berlin" -> "Tokyo"; "Virtual Hard Disk was created by Microsoft" -> "which company?\nWhat is the answer?").
- **The edits have sizeable side effects before any undo.** The edited model changed 125 of 300 unrelated probes and 327 of 500 hard negatives (exact match on 8 greedy tokens), which is the harness's locality of 0.58 / 0.35. This was in the summaries all along but not in the post. It fits the dev-set spectrum result: the edit is rarely the top component of the matrix. It does not affect the undo results (restore and subtract return all of these to base).

Write-up: the blog post's Data bullet now gives both side-effect counts and the norm range (DOC_EDITS 08:10).

Not checked: whether EasyEdit's ROME includes the r-ROME prefix fix. r-ROME as a second editor is on the list of possible follow-ups.

## 2026-11-02 (21:30): Independent review of the blog post; fixes

A fresh subagent that had not seen the work checked every number and claim in the blog post (Claude Doc rev 20) against `results/` and the arXiv paper. Its scripts were in the session scratchpad; nothing in the repo was changed by it.

Numbers: all headline figures recompute exactly from the files, with no wrong numbers. That covers exact revoke, leak and ES for every undo mode and both controls; the MMD rejection counts; the CIs; the dev table; the Result 1 figures; and both Youssef et al. quotes (verbatim, Sec. 5.3 "Reversal"). The ES figures come from the margins runs, which use the same deltas file and case ids as the exact-revoke runs and give byte-identical outputs.

Claims fixed in the post (rev 20 -> 35, DOC_EDITS 21:30):
- The TL;DR put the 68% (q=7-10) next to the leak and ES figures (q=3) without saying the settings differ. Both are now named.
- "Out of reach by design" became "at this setting". The data shows output changes at q=3 only.
- MMD: "every one of the 8 control rejections is also rejected after the undo" is partly built in, because both runs compare against the same base sample (seeds 1000+i). Two of the 8 are also rejected for restore. The post now rests on 45 vs 8 rejections and a mean MMD about 9 times the control's, and states that caveat.
- "The README gives the commands for each run" was false. It now reads "LOG.md records the command for each run", and the post adds that the edit files are not committed (regenerate them with the export script, about 2 h).
- "The full list is in the repository" was false: the labels existed only as prose in the 14:15 entry. They are now committed as `labels/svd3_q3_cf100_leaks_labelled.json` (130 rows: 51 identical_to_edited, 76 edited_answer_new_text, 3 other), built from that entry's decisions and checked against its counts.
- Wording: the leak definition (any mention of the target in the 8 tokens, where base did not mention it); ES (mean per-token log-probability); the dev-table metrics differ from the paper's (their editing accuracy is next-token agreement with the edited model); the 86% vs 100% subtract results (several factors differ: bf16 model, layer 4, our editor); run times; "before scoring any test edit". CIs added for the control leak (0.06-2%) and the control ES (15-31%).
- `run_rome.py` now records `max_new_tokens` and `svd_q` in the run meta. Earlier runs relied on the default of 8, which their meta doesn't show.

Top reviewer attack, not yet addressed: the test set was run only at q=3, the best setting by our own criterion, where the dev set keeps the edit in 53% of cases. At the paper-like q=7-10 it is 26%, so the leak there is likely lower. Decision: run the test set at q=10 with its own control (task #19) before the Nov 9 email, and report both settings. The post's Limitations now say this.

Not checked by the reviewer: whether our config matches the authors' Qwen2.5-7B YAML, and the Caddeo, Gao, Jiang and Meng citations. Stale file noted: `results/20261102T143500_ci_headline.json` still shows [0, 0] leak CIs for restore/subtract, from before the Wilson fallback. The post doesn't use those rows.

## 2026-11-02 (19:00): MMD control result: truncation alone barely moves the sampled distribution

Run (prediction in 17:30): `results/20261102T180312_stat_undo_ee_cf100_nulledit.json` (about 37 min). Its base-vs-base check rejected 3/100, the same as the 14:15 run.

| Comparison (100 cases, alpha 0.05) | Rejected | Median p | Mean MMD |
| --- | --- | --- | --- |
| Base vs base (this run) | 3 | 0.42 | 0.0003 |
| Truncation control, no edit (q=3) | **8** (Wilson CI 4-15%) | 0.38 | 0.0011 |
| SVD undo of the real edit (14:15 run) | 45 (CI 36-55%) | 0.08 | 0.0103 |

Case by case: 8 cases are rejected for both the control and the undo, 37 for the undo only, 0 for the control only, and 55 for neither.

Against the predictions:
- Wrong on the first: the control was predicted at 15-45 rejections and gave 8, close to the 3-7% seen for base-vs-base and restore. Truncation changes 40% of greedy probes but shifts the sampled distribution only slightly. The likely reason is that greedy outputs flip on near-ties, which hardly change the distribution.
- Right on the second: the undo is rejected far more often than the control (45 vs 8), with about 9 times the mean MMD.
- The third (the test cannot separate edit from truncation) did not happen.

What this means:
- The distribution result is not confounded the way exact revoke was. Most of the 45% is the surviving edit: 37 of 45 rejected cases are rejected only when the edit was there. The post can state the MMD result with the control beside it.
- Taken together, the three measures that survive the control are the leak (43% vs 0.3%), ES (0.69 vs 0.22) and MMD rejection (45% vs 8%). Exact revoke on all probes (1 vs 0 of 100) does not survive it.
- Correction to the 17:50 entry: "Jiang et al. report 39-57% continuation agreement" came from the external research report. Per the draft's reading of their Table 5 (Nov 2), the range is 37-57%, and it is measured on edited models with the first token forced, not after a reversal. So it is not an overlap with our reversal result. The draft cites it as the next-token assumption we test.

## 2026-11-02 (17:50): Direction check: keep retractbench, frame it as research, not a startup

Question asked: is this project the best route into the field, or should it pivot? Decision: keep it, narrow it, and change the framing. Master Plan v4 (Drive) replaces v3.

Why keep it:
- It already reproduces a published ICLR 2026 method from the authors' own code (first-token rate 68% on dev vs their 62.9%) and adds a measurement they didn't make. A careful public replication with a new result is the clearest evidence of research-engineering skill available without a degree.
- The first public output is about a week away. A pivot now would replace a nearly finished result with nothing.
- The core claim has survived its first hard control (17:20): the leak (130/300 vs 1/300 under truncation alone) and the probability scores (ES 0.69 vs 0.22) are the edit surviving, not truncation damage.

What changes:
- **Framing.** Research and an open benchmark, not a company. The landscape and research reports found no commercial edit-rollback products and no procurement demand. The month-3 "demand conversations" are dropped from the plan; the month-9 decision gate stays.
- **Contribution.** "SVD reversal isn't exact" is not new on its own (Youssef et al. report KL 1.53 on Qwen2.5-7B; Jiang et al. report 39-57% continuation agreement). The contribution is the cross-method comparison: exact by storage (restore, subtract), approximate by forensics (SVD), and editors that claim exact undo by design (GRACE rollback, LoRA-per-edit, SoLA-style routing), none of which has been tested against base beyond the edited prompt.
- **Experiment order after the post:** (1) MMD power calibration at 10/20/50 samples per probe, with Benjamini-Hochberg across edits and a pooled test; (2) GRACE rollback through EasyEdit, single edit, then one edit removed from 10 and 100 sequential edits; (3) LoRA-per-edit, unmerged and merged-then-subtracted; (4) MEMIT batch-minus-one and AlphaEdit sequential removal, scored against the batch-minus-one model; (5) a second model family at 1-3B (Llama-3.2 or Gemma-2) in bf16. 7B goes to a rented GPU in bf16 only if a mentor or funder asks; 4-bit stays a robustness check.
- **Applications.** SPAR Spring 2027 (opens around December, per sparai.org; date unverified), then MATS Summer 2027 (window date unverified). Anthropic Fellows if a cohort opens. Funding to try: BlueDot Rapid Grants, Transformative AI Fund (16:30 entry).
- **Writing.** Report what was measured, with the criterion and the denominator. No "catastrophic" or "unprecedented"; Youssef et al. already say recovery is partial, so the post measures how partial.

Open before the post: the MMD null-edit control (17:30 predictions) and the write-up's reconciliation of the 86% (simplified editor) vs 100% (genuine ROME, fp32) subtract results, which the blog draft now explains (DOC_EDITS 17:05).

## 2026-11-02 (17:30): Control for the distribution test (predictions)

Why: the 14:15 MMD run rejected "same as base" for the SVD undo in 45/100 cases. The truncation control (17:20) showed that truncation alone changes 40% of greedy probes, so part of that 45% may be truncation damage.

Run: `run_stat_undo.py --tag ee_cf100_nulledit --deltas data\easyedit_rome\cf100.pt --dtype float32 --modes svd --svd-q 3 --null-edit`. Settings are otherwise the 14:15 run's: 10 samples per probe, 20 tokens, 1,000 permutations, alpha 0.05, and the same base-sample seeds. Code: `--null-edit` added to `run_stat_undo.py`, the same zero-update replacement as in `run_rome.py` (mechanics covered by `test_null_edit_control`).

Predictions:
- The control is rejected well above the 5% null, because truncation alone shifts 40% of greedy probes. Range: 15-45 of 100.
- It is rejected less often than the real SVD undo (45/100), and its mean MMD is lower than the undo's 0.0103, because the surviving edit adds to the shift.
- If the control is rejected about as often as the undo (35 or more of 100), the MMD test cannot separate a surviving edit from truncation at this power, and the post says so.

Note: the headings of the two entries below were corrected from 17:15 and 17:45 to 17:00 and 17:20. They had been labelled ahead of the clock. DOC_EDITS.md times were corrected the same way.

## 2026-11-02 (17:20): Control result: truncation alone changes every case; the leak survives the control

Run (prediction in 17:00): `results/20261102T231932Z_null-edit-svd3_ee_cf100_nulledit_L5_iso.json` (15.5 min), plus `results/20261102T2340_null_svd_compare.json` from `compare_null_svd.py`. Same 100 cases, 11 probes and 8 greedy tokens as the SVD test run.

| | SVD undo of the real edit (q=3) | Same truncation, no edit (control) |
| --- | --- | --- |
| Every probe equals base (exact revoke) | 1 of 100 | **0 of 100** (Wilson CI 0-3.7%) |
| Probes equal to base | 417 of 1,100 (38%) | 659 of 1,100 (60%) |
| Target leak (edited prompt + paraphrases) | 130 of 300 (43%) | 1 of 300 (0.3%, CI 0.06-1.9%); 0 excluding answers naming the true object |
| CounterFact ES after undo (base 0.19) | 0.69 | 0.22 |
| PS / NS after undo (base 0.20 / 0.81) | 0.67 / 0.70 | 0.20 / 0.80 |
| Undone model equals control on every probe | 0 of 100 | - |

Against the predictions:
- Truncation alone changes the model even more than predicted: 0/100 exact, against a predicted 5-40. With 11 probes per case, at least one probe changed in every case, and 40% of all probes changed.
- Leak near 0 for the control: as predicted (0.3%).
- Undone model equals the control on all probes in 0/100 (predicted under 20). Per probe, the undone model agrees with the control (439) slightly more often than with base (417), as predicted, but the margin is small.

What this means:
- **The exact-revoke figure for SVD (1/100) is not evidence that the edit survived.** At q=3, truncation cannot return the model to base even when there is nothing to undo. This stands as a finding in its own right: by construction, the method removes part of the base matrix, so it cannot restore the model exactly. But it is not the headline about the edit.
- **The evidence that the edit survives is the leak and the probability scores.** Those barely move under the control (43% vs 0.3% leak; ES 0.69 vs 0.22). On a per-probe basis, the undone model's extra distance from base beyond the control (60% -> 38% of probes equal to base) is also the edit's doing.
- **The MMD result (45/100 rejected) is confounded the same way** until the control is sampled too. Decision: label it as confounded, and add a null-edit option to `run_stat_undo.py` as a follow-up.
- Write-up: the blog post's TL;DR and results are revised to lead with the leak and ES, and they report the control. The "1 of 100" figure stays, with the control's 0 of 100 next to it.

## 2026-11-02 (17:00): Control: SVD truncation on the unedited model (predictions)

Why: the external research report (Drive, "retractbench Research Direction", Nov 2) raised a reviewer's first question: is 1/100 exact revoke a failure to remove the edit, or what dropping q=3 singular components does to any model? This control separates the two.

Run: `run_rome.py --tag ee_cf100_nulledit --deltas data\easyedit_rome\cf100.pt --dtype float32 --modes svd --svd-q 3 --null-edit`. The edits are replaced by zeros, so "after_revoke" is the unedited model with layer 5's top 3 singular components dropped. Same 100 cases, 11 probes and 8 greedy tokens as the test run. Then run `scripts/compare_null_svd.py` against `results/20261102T185248Z_easyedit-rome-svd3_ee_cf100_L5_iso.json`.

New code: `run_rome.py --null-edit` and `scripts/compare_null_svd.py`, plus a tiny-model test (`test_null_edit_control`). No metric definition changes.

Predictions:
- Truncation alone changes the model. Null-SVD returns every probe to base in well under half the cases (somewhere around 5-40 of 100). At q=3 the dropped directions belong to the base matrix too (top singular value 6.51 vs edit norms 2.3-5.9 on dev), and the dev sweep showed base answers changing as q grows.
- Leak: null-SVD target leak near 0 (at most 2% of target probes), against 43% after the real undo. If so, the leak is the edit surviving, not truncation.
- The undone model matches null-SVD on all probes in few cases (under 20 of 100), because the edit often survives. Per probe, edited-SVD agrees with null-SVD more often than with base.
- What changes in the write-up: if null-SVD exact is low, the 1/100 figure mixes two effects (edit left behind, model damaged by truncation). The post then leads with the leak and the probability score, which this control cannot explain away, and states the null-SVD rate next to 1/100.

## 2026-11-02 (16:30): Second Gemini report triaged; blog post drafted

Two Drive docs were read: "LLM Edit Reversal Research Plan" (a Gemini Deep Research report) and "projectfindingsarxiv" (alternatives to arXiv). Their claims are treated as leads and checked against primary sources. Corrections:
- Gemini attributes "semantically similar ... not identical" and "the decrease in editing accuracy is higher than the increase ..." to an OpenReview reviewer. Both are in Youssef et al.'s own Sec. 5.3 (arXiv:2505.20819v2). The OpenReview page could not be opened (browser check). The paper also says, verbatim: "suggesting that the method is more effective in removing the edit than in recovering the original object." That sentence is now quoted in the draft and the blog post.
- Its "new since September 2026" list is mostly older work. The Butterfly Effect paper is from Feb 2024 (arXiv:2402.09656) and DeltaEdit from May 2025. Caddeo et al. was published 1 July 2026 (DOI 10.3390/app16136567), not October. "Persona Hierarchy Model" is sourced only to a ResearchGate profile, so it is unverified and not cited. Jiang et al. (Sept 2026) is the only genuinely new item, and it was already cited.
- Funding: the LTFF is closed to new applications (Manifund funder bulletin, as of Oct 15, 2026). The bulletin also lists three options Gemini missed, all rolling and open to individuals: the Transformative AI Fund (LTFF successor, $10k-150k), BlueDot Rapid Grants (up to $20k), and the GTR AI Safety Fund. Gemini's "fellowship closed November 30, 2026" cannot be right as of today. Its AIAF entry comes from a third-party listing.
- Confirmed: since Jan 21, 2026, a new arXiv author with no papers needs a personal endorser (arXiv blog). Candidate endorsers: Youssef, Zhao, Bau, Ningyu Zhang. Ask Youssef or Zhao first, after the preview email.
- Gemini's "novelty: not found" result comes from one search. It is not proof, and it changes nothing in the post's hedged wording.
- From the arXiv-alternatives doc: Papers with Code was shut down by Meta in July 2025 (it redirects to Hugging Face), so it is dropped. Zenodo is adopted: link the repo once, and each tagged GitHub release gets a citable DOI. Affiliation: list Maestro, not "independent". The doc's template endorsement email is not used as written.

Blog post drafted as a new Claude Doc, "The Fact Comes Back, the Model Doesn't (blog post draft)", leading with Result 2 (decision 15:45). The technical draft stays as the full reference. The post contains no numbers that are not in the technical draft.

## 2026-11-02 (15:45): Write-up decisions; Youssef et al. wording checked

Decision: the blog post leads with Result 2, the reproduction of Youssef et al.'s SVD-truncation reversal: consistent with their first-token rate (68% on 19 dev edits vs their 62.9% on Qwen2.5-7B), but an exact multi-token return to base in 1 of 100 test edits.

Decision: send Youssef et al. the reproduction 3-4 days before posting, with a fixed post date. Proposed schedule: email Mon Nov 9, post Thu Nov 12.

Checked against arXiv:2505.20819v2:
- Sec. 5.3: "For reversal accuracy, we approximate the model's outputs using the next token prediction." The headline Qwen2.5-7B ROME number is 62.90% at k=10 (Table 2), on 310 instances from 31 relations. The 5-token greedy generations are for the qualitative examples (Table 4) only.
- The 15:00 entry's paraphrase is correct and can now be quoted.
- One draft line overstated the paper. It said the paper "reports that Qwen2.5-7B's output distribution is not fully recovered"; the paper does not say this. It reports KL divergence to the original model (Table 3), which stays highest for Qwen2.5-7B (1.534 at k=15). The draft now states the KL figure instead.

## 2026-11-02 (15:25): Caddeo-style margin scores on 100 genuine ROME edits

Run: `run_rome.py --tag ee_cf100_margins`, restore/subtract/svd at q=3, cf100, fp32, 8 greedy tokens. Results in `results/20261102T2045*`, `T2057*`, `T2110*` (`_ee_cf100_margins_L5_iso`) and `20261102T151004_rome_ee_cf100_margins.json`. About 35 min.

| Stage | ES (prompt prefers new target) | PS (paraphrases) | NS (hard negatives still prefer true object) |
| --- | --- | --- | --- |
| base | 0.19 | 0.20 | 0.81 |
| after edit | 1.00 | 0.98 | 0.61 |
| after undo: restore | 0.19 | 0.20 | 0.81 |
| after undo: subtract | 0.19 | 0.20 | 0.81 |
| after undo: SVD q=3 | **0.69** (Wilson CI 0.59–0.77) | 0.67 | 0.70 |

- Existing metrics reproduced exactly: SVD revocation_exact 0.010, leak 0.433 and 0.427, restore/subtract 1.000 and 0.000. The runs are deterministic.
- The base model already prefers the counterfactual target on 19 of 100 prompts, so "ES back to base" is the right yardstick, not "ES = 0".
- SVD at q=3 on Caddeo's measure: in 51 cases the prompt preferred the true object before the edit and still prefers the edit's target after the undo. NS after the undo is below base in 25 cases.
- So the SVD reversal looks partial on every criterion we have. It doesn't pass on the log-probability measure and fail only on ours.
  - The first-token criterion is the most lenient (68% on dev). The probability comparison is stricter, because a target can stay more probable than the true object even when the greedy first token is back.
- Prediction check: ES after the SVD undo was predicted at about 0.5 and came out 0.69, so the reversal is worse than expected. The rest: restore/subtract equal to base; after edit ES ≈ 1.0 (got 1.00), PS ≈ 0.8 (got 0.98, higher than predicted), NS ≈ 0.8 (got 0.61, lower); base ES 0.1–0.2 (got 0.19).
- Independently reviewed at 15:20: all 68 numbers matched and no code bugs were found. Wording fixes:
  - ES/PS/NS are CounterFact's probability scores (Meng et al. 2022), the family Caddeo et al. report, not a measure of Caddeo's own; their exact variant may differ.
  - They are yes/no comparisons, not margins. The code name `margin_scores` stays, but text calls them "probability scores".
  - "First-token is the most lenient criterion" compares different sets and q values, so it is indicative only.
  - Ties: ES/PS use a strict `>` and NS counts a tie as preferring the true object, which differs from ROME's code only on exact ties.

## 2026-11-02 (15:05): independent check of the write-up draft; corrections

A fresh reviewer (a subagent that hadn't seen the drafting) checked the draft against the result files, working on a clone of commit 5ae8289, and against the cited papers. About 75 numbers were checked and 68 matched. The headline numbers all held. These were wrong, and are now fixed in the draft:

- **Token count. This corrects the 13:00 entry above.** The 100-case test runs (restore/subtract/svd3) and the Nov 1 Result 1 runs used `run_rome.py`'s default `--max-new-tokens 8`, not 5. Only the dev sweep compared 5 tokens. So the 13:00 entry's "all probes, 5 greedy tokens" should read 8. This makes the criterion stricter, not looser.
  - The run JSONs don't record max_new_tokens. Add it to the run meta (next code change).
- **Leak denominator.** 43% is 130 of the 300 target probes (edited prompt + 2 paraphrases per case), not 43% of all 11 probes per case.
- **Result 1 subtract row.** The 14 non-exact cases changed one probe each, of mixed kinds: 1 edited prompt, 5 paraphrases, 5 unrelated, 3 hard negatives. So unrelated changed = 5/300 and hard negatives changed = 3/500. The draft had said "one unrelated probe in each".
  - The La Plata → Rosario flip is on a paraphrase, not on the prompt quoted.
- **Spectrum (dev, 20 edits).**
  - The edit is among the top 4 components in 15 of 20 cases (`best_component` is 0-indexed), not "1–3".
  - Alignment is 0.4–0.84 in 14 of 20 cases; the other 6 are 0.01–0.34, and two are about 0.
  - The 08:25 entry's "usually components 1–3, alignment 0.4–0.84" overstated this.
- **Quotes.**
  - The Youssef Sec. 5.3 wording was not verbatim, so it's paraphrased now. Check against the PDF before quoting.
  - Caddeo: "is not considered a perfect inverse", "behavioral recovery".
- **Minor.**
  - Inverse-to-true exact revoke is 0.00, not ≤ 0.01.
  - "About a third" changed is 27–36%.
  - 2410.12586 has no confirmed venue (NAACL dropped).
  - Gao et al.: fine-tuning on out-of-distribution code data, not "full fine-tuning on unrelated data".
- **Wording softened.**
  - "Reproduces their numbers" became "consistent with" (13/19, CI 0.46–0.85).
  - q=3 was chosen on 19 cases.
  - "At least 45%" became "45 of 100 (CI 36–55%), at limited power".
  - "Qwen was their hardest model" is now stated as the observable facts.
- **Jiang et al. Table 5, read.** It concerns edited models, not reversal. It argues next-token optimisation suffices because the continuation follows the first token (37–57% continuation agreement once the first token is forced). It's cited as the assumption we test, not as support. Gemini's reading was wrong.
  - Youssef and Jiang also report KL divergence, so our novelty claim is "exact multi-token matching + significance test", not "first distributional check".

Lesson: drafting numbers from LOG summaries instead of from the files let a wrong token count and a mis-described table row through. Check against files before anything goes public.

## 2026-11-02 (14:50): confidence intervals; Caddeo-style margin scores added (metric change)

**Confidence intervals** (`scripts/ci_headline.py`, new; `results/20261102T143500_ci_headline.json`)
- Wilson 95% intervals for rates counted once per case. The leak rate is per probe, so its interval comes from a bootstrap over cases, because the 3 probes of one case aren't independent. When the count is 0, the script uses a Wilson interval over cases instead, since a bootstrap of all-zero data gives a misleading [0, 0].
- Test set, 100 cases:
  - exact revoke: restore and subtract 100/100 [0.963, 1]; SVD q=3 1/100 [0.002, 0.054]
  - target leak: SVD q=3 130/300 probes [0.347, 0.523]; restore and subtract 0 (≤ 3.7% of cases)
  - MMD rejects: SVD 45/100 [0.356, 0.548]; base vs base 3/100 [0.010, 0.085]; restore 7/100 [0.034, 0.137]; subtract 3/100 [0.010, 0.085]
- Dev sweep (19 edits), so the intervals are wide:
  - first-token reversal at q=7–10: 13/19 = 0.68 [0.46, 0.85]. This interval contains the paper's 62.9%, so "consistent with their number" is the honest wording, not "matches".
  - all-5-token reversal at q=3: 6/19 = 0.32 [0.15, 0.54]
  - Choosing q=3 on 19 cases is a weak choice; the neighbouring q values are within noise. The test-set result at q=3 (1/100 exact) is far from any of them, though.

**Metric change: CounterFact margin scores** (`harness.margin_scores`, `CaseResult.margins`, `RomeEditor.logprob`)
- What: ES/PS/NS (Meng et al. 2022), the measures Caddeo et al. use for edit-then-revert.
  - ES: does the edited prompt prefer the new target over the true object?
  - PS: the same, on the paraphrases.
  - NS: do the hard negatives (CounterFact neighbourhood prompts) still prefer the true object?
  - Comparison by mean log-prob per token, as in ROME's evaluation.
- Scored at three stages (base, after write, after revoke). Summary keys are `es_base` … `ns_after_revoke`.
- Only editors with a `logprob()` method get these scores, so GRACE results are unchanged. No existing metric changed.
- Why: so the write-up can give their criterion and ours on the same edits.
- Tests: `tests/test_margins.py` (6 tests: clean undo, bleed, trace, no target_true, editor without logprob, summary keys), plus 2 tiny-model tests in `test_rome_tiny.py`. One checks logprob against scoring one token at a time; the other checks that an edit raises the target's log-prob and restore puts it back. 79 tests pass.
  - While writing the summary test, a fake editor that leaves its edit in and has no reset() showed up correctly as a raised base ES in the next case.
- Running: `run_rome.py --tag ee_cf100_margins`, restore/subtract/svd q=3 on cf100 (log `results/logs/ee_cf100_margins.log`).

**Predictions before the margins run**
- restore and subtract: after-revoke ES/PS/NS equal to base exactly.
- edit: ES ≈ 1.0, PS ≈ 0.8, NS ≈ 0.8.
- base: ES ≈ 0.1–0.2. The base model rarely prefers a counterfactual target, but the base model gave the true object greedily on only 15/100 prompts, so not 0.
- SVD q=3 after revoke: ES around 0.5, in line with "edit kept" at 0.53 on dev and 130/300 leaking probes. So SVD should look partial on Caddeo's measure too, not near-perfect. NS after SVD a little below base.

## 2026-11-02 (14:15): distributional undo test on 100 cases; SVD leaks hand-labelled

**Distributional test** (`run_stat_undo.py`, cf100, the same genuine EasyEdit ROME edits, q=3, fp32; per probe 10 samples × 20 tokens at temperature 1; Hamming-MMD permutation test; `results/20261102T135148_stat_undo_ee_cf100.json`, about 59 min)

| Comparison | Rejected at α=0.05 | Median p | Mean MMD |
| --- | --- | --- | --- |
| base vs base (null) | 0.03 | 0.421 | 0.0003 |
| restore | 0.07 | 0.435 | 0.0007 |
| subtract | 0.03 | 0.467 | 0.0002 |
| SVD q=3 | 0.45 | 0.081 | 0.0103 |

- Calibration: restore puts back bit-identical weights, so restore vs base is a second null run. 3% and 7% out of 100 tests are both consistent with the nominal 5%.
- SVD truncation is detectably different from base in 45 of 100 cases, with a mean MMD about 30× the null's. With only 10 samples per probe the test has limited power, so 45% is a lower bound. Greedy matching found 99 of 100 cases changed.
- No prediction was recorded for this test beforehand, so it must not be described as predicted.

**SVD q=3 leak flags, hand-labelled** (`scripts/list_leaks.py`, new; it uses `harness.leak_flags`, so the flags are exactly the counted ones)
- 130 flags = 130 of 300 target probes (0.433), in 54 of 100 cases.
- 51 flags: the after-undo output is identical to the edited model's. The undo did nothing on that probe.
- 76 flags: the output still gives the edited answer and only the continuation differs ("Toronto." → "Toronto, Canada."; "Paris, France, and was known for" → "Paris, France, and was a famous").
  - In cf19723 ("Carl Flesch worked in"), the edited model didn't say Paris on that paraphrase, but the undone model does.
- 3 flags are something else:
  - cf6025: "a mixture of French and English". The true object and the target are both present, so this is a partial trace.
  - cf17979: "writes in the Irish Times". The target word appears in a different sense.
  - cf10819: "Chrysler LLC, a subsidiary of Fiat Chrysler". Ambiguous for a real-world fact.
- Conclusion: the SVD "leaks" are not subtle traces. On 127 of 130 flagged probes the edited fact is still being asserted, so q=3 often doesn't remove the edit there at all. That fits the dev sweep, where the edit was kept in 53% of cases at q=3. Larger q removes more of the edit but changes more of the base model's answers (LOG 08:25).

## 2026-11-02 (13:00): 100-case scoring, power cut, Gemini report, plan change

**Power cut (mid-morning)**
- The 100-case EasyEdit export died at 18/100 and kept nothing, since it only saved at the end. It was re-run 10:09–12:15: 100/100 edits made, every one with rewrite_acc 1.0, and the weights checked as restored after each case.
- Fix: a checkpointed export (atomic `<tag>.partial.pt` written after every case, resumes when run again, `--fresh` to restart) is in `scripts/easyedit_rome_export_ckpt.py`. **Not yet run.** Test it with `--limit 2`, then interrupt and resume, before it replaces the current script.

**Result: genuine ROME edits from the authors' EasyEdit, 100 CounterFact test cases, Qwen2.5-1.5B, fp32, layer 5, all probes, 5 greedy tokens**

| Undo | revocation_exact | target_leak_after_revoke | target_leak_excl_true |
| --- | --- | --- | --- |
| restore (copy back) | 1.000 | 0.000 | 0.000 |
| subtract the update | 1.000 | 0.000 | 0.000 |
| SVD truncation, q=3 (Youssef et al.) | 0.010 | 0.433 | 0.427 |

- Edit quality with this config: edit_success 0.99 (loose 1.00), paraphrase 0.805, locality 0.583, locality_hard 0.346.
- Results: `results/20261102T183353Z_*restore*`, `20261102T184305Z_*subtract*`, `20261102T185248Z_*svd3*`. An earlier svd3 run (`20261102T180339Z`, commit 280a2bb) gives identical summary numbers, so the replay is deterministic.
- q=3 was chosen on dev20 as the best 5-token setting (LOG 08:25). By our criterion, SVD truncation returns the model to base on 1 case in 100, and the edited target still shows up on 43% of probes after the "undo". This says nothing against their next-token numbers, which we reproduced on dev20. It shows that the two criteria disagree.
- Not yet looked at: per-case leaks by hand (the leak count over-counts some real-world facts, LOG 09:30), and the distributional test (`run_stat_undo.py`, running; restore and subtract should come out at the base-vs-base null).

**Gemini research report (Drive, "Literature Research & Verification Documentation", Nov 2), spot-checked**
- Holds up: Youssef et al. score the next token only. Caddeo et al. score log-probability margins (ES/PS/NS). Jiang et al. (arXiv 2609.02091) Table 5 exists, with continuation agreement 39.2–57.3%.
- Overstated: "Caddeo asserts full reversibility". The paper says "behavioural recovery" and "not a perfect inverse". Treat it as a fair comparison, not a foil.
- Needs reading before citing: Jiang Table 5 is in a section on whether next-token optimisation suffices, and its first-token column is 0.00, so it may describe edited models rather than reversal. Zhang et al. (2601.11042) is about sequential editing at scale, and its "62.6%" figure wasn't found.
- Wrong: it describes Gao et al. as a KL/Wilcoxon test (it is an MMD test on samples), it says EDPB accepts procedural safeguards in place of technical proof (the opinion asks for anonymity to be demonstrated), and it dates the Rite Aid order to 2024 (it is Dec 2023).
- Unchecked: the venues of Jiang and Zhang, the workshop deadlines (TTU at ICLR 2027, Insights, TrustNLP), NIST/ISO, and the arXiv endorsement details.

**Plan change (decision)**
- Publish the write-up as a blog post with the code on GitHub during Nov 9–15. arXiv follows once an endorser is found; we don't wait for one.
- Next: add Caddeo-style log-probability metrics to the harness, so the write-up can give both their criterion and ours on the same edits. As with every metric change, it gets a LOG entry and a test.

## 2026-11-02 (09:30): leak check for real-world facts, a second count (not a replacement)

**Metric change** (harness.py, per CLAUDE.md): `target_leak_after_revoke` is unchanged. Added `target_leak_excl_true`: same, but a probe does not count as leaking if its after-revoke answer also mentions the true object. Both use the new `harness.leak_flags`. Without a `target_true` (fictional cases) the two are identical. New tests in `tests/test_harness.py` (target inside a true answer, target alone, target already in base, no target_true); 71 tests pass.

**Re-scored the cf100 layer-4 runs from stored outputs** (`scripts/rescore_leaks.py`, `results/20261102T085843_rescore_leaks.json`; original run files untouched). The recomputed plain counts match the stored ones exactly (subtract 0.000, inverse 0.020, inverse-true 0.020), so the refactor did not change the old metric.

| run | leak (plain) | leak excl. true | leaky cases: plain / strict |
| --- | --- | --- | --- |
| subtract | 0.000 | 0.000 | 0 / 0 |
| inverse (base tokens) | 0.020 | 0.017 | 5 / 4 |
| inverse (true object) | 0.020 | 0.010 | 5 / 2 |

**The stricter count is not simply better.** Of the three inverse-true cases it drops: cf10819 "Fiat Chrysler Automobiles" is a correct answer (right to drop); cf18105 "chemistry, not mathematics" is a genuine trace of the removed edit (wrong to drop); cf4267 "French, English, and Latin" is ambiguous. So one false positive fixed, one false negative introduced. Neither string rule decides this correctly.

**Decision for the write-up:** report the plain count, list every leaking case with its text, and hand-label each (true answer / trace / ambiguous). At this sample size (5 cases per run) a labelled list is more honest than either automatic number. A model-based or answer-slot check is possible later but not needed now.

## 2026-11-02 (09:10): how Youssef et al. score reversal (settled), and our dev result reproduces theirs

From the paper (arXiv:2505.20819v2, Sec. 5.3): reversal and editing accuracy are agreement between the model's output after the intervention and the original (or edited) output, and "for reversal accuracy, we approximate the model's outputs using the next token prediction". So **their reversal accuracy is first-token**. Their headline Qwen2.5-7B ROME number, 62.90% at k=10 (Table 2, 310 successful edits, 31 relations), is first-token, with editing accuracy still 27.42% at that k. They generate 5 greedy tokens only for the qualitative examples (Table 4), which they describe as "semantically similar", not identical, to the originals.

**Our dev sweep on Qwen2.5-1.5B, same criterion:** first-token reversal 0.68 at q = 7-10 with the edit still present in 26%. That matches their 7B numbers closely, so the setup reproduces their method faithfully. On our stricter criterion (all 5 tokens equal to base) the best is 0.32 at q = 3.

Their own Table 3 also shows Qwen2.5-7B's output distribution is not recovered: mean KL to the original model on the edited prompt drops from 8.99 to 1.53 at best, not to ~0. That is consistent with the return-to-fact vs return-to-model point, from their own numbers.

**Correction to this morning's triage of the Gemini notes:** "paper scores first token only" was filed as wrong. The paper says it does score the first token. The other items in that list are unaffected.

**For the write-up:** compare like with like. Report our first-token number next to theirs (reproduction), then the 5-token and all-probes numbers as the stricter return-to-model view.

## 2026-11-02 (09:00): statistical undo test, cross-checked against the authors' package

New `src/retractbench/equality.py`: the Hamming-MMD two-sample test of Gao, Liang & Guestrin, "Model Equality Testing" (ICLR 2025, arXiv:2410.20247), plus `scripts/run_stat_undo.py`, which samples every probe at temperature 1 (10 samples per prompt, 20 tokens) from the base model twice (the base-vs-base null) and once after each undo, and tests base vs post-undo. `restore` is the control and should reject at about alpha. This is a new metric module; nothing in harness.py changed.

**A discrepancy found while cross-checking.** The paper's eq. 4 averages kernel values over all sample pairs (N(N-1), N^2). Their package (`model_equality_testing.tests._mmd`) averages only over pairs that share a prompt. With several prompts these are not proportional. Their reported results come from the package, so equality.py follows the package (the docstring says so). Both give valid permutation tests.

**Cross-check** (`tests/test_equality_crosscheck.py`, needs `model-equality-testing==0.0.2`, MIT; a test-only dependency): our statistic equals theirs to 1e-9 on multi-prompt data with and without a shift; permutation p-values agree within 0.05 at 2000 permutations. Also tested: the kernel formula by hand, false-positive rate near alpha on equal distributions, and detection of a clear shift.

## 2026-11-02 (08:25): real ROME edits, dev-set q sweep

`results/20261102T082232_svd_q_sweep_easyedit_counterfact_dev20_seed1.json`, log in `results/logs/`. 20 dev cases, EasyEdit ROME (their config, layer 5), scored in fp32. 19/20 edits succeed by both their rewrite_acc and our strict match (cf16057 fails both, skipped). The 100-case export was stopped at 4/100 to run this first.

**Spectrum (prediction 1: wrong).** The original layer-5 matrix's top singular value is 6.51. No real edit exceeds it (spectral norms 2.33-5.88). The edit is the #1 component of the edited matrix in only 1/20 cases. But real edits do sit much nearer the top than our simplified ones: the best-aligned component is usually #1-#3 with alignment 0.4-0.84 (ours: #5-#14, 0.06-0.42). The two weakest edits (cf930, cf12831, norms 2.3-2.5) align with nothing (0.01-0.05).

| q | reversal, 5 tokens = base | reversal, 1st token = base | edit kept |
| --- | --- | --- | --- |
| 1 | 0.05 | 0.05 | 0.95 |
| 2 | 0.05 | 0.16 | 0.84 |
| 3 | **0.32** | 0.42 | 0.53 |
| 4 | 0.21 | 0.58 | 0.37 |
| 7-10 | 0.21 | **0.68** | 0.26 |
| 20 | 0.11 | 0.68 | 0.21 |

Best q by the 5-token criterion: **q = 3 (0.32, 6/19)**. By first token alone the method looks twice as good (0.68 at q = 7-10). That gap matters for comparing with the paper's 62.9% on Qwen2.5-7B: their `reversing_single_edits.py` stores 5-token predictions, but how the paper scores them is not in the repo. Check before citing either number against theirs.

**Prediction 2** (best-q reversal 40-70%, central 50%) is not settled until the test set runs, but the dev result (0.32) is below the range on the 5-token criterion and inside it on the first-token one.

**Next:** resume the 100-case export (about 3 h at ~105 s/edit), then `run_rome.py --deltas ... --modes restore subtract svd --svd-q 3` for the all-probes comparison, and the statistical undo test (`scripts/run_stat_undo.py`).

## 2026-11-02 (morning): real ROME edits from the authors' EasyEdit, setup and predictions

**Setup.** Their repo (github.com/paulyoussef/trace-and-reverse, commit d783bc1) is cloned to `D:\trace-and-reverse` with its own venv (Python 3.10, torch 2.0.1+cu118, transformers 4.46.2), because their EasyEdit pins an older transformers than ours. Editing and scoring are split:
- `scripts/easyedit_rome_export.py` (their venv) calls their `BaseEditor.edit` exactly as `reversing_single_edits.py` does, wraps their `execute_rome` to save each case's two ROME vectors, and checks the matrix is back to its original values after every case. It records their own `rewrite_acc` (their script skips edits below 1.0).
- `editors/precomputed.py` (`PrecomputedRomeEditor`) replays those updates in our harness with the existing restore / subtract / svd undo modes. Mechanics tests in `tests/test_precomputed_tiny.py`.
- `run_rome.py` and `sweep_svd_q.py` gained `--deltas` and `--dtype` (their edits are made on an fp32 model, so we score in fp32 too). The sweep now also reports where each edit sits in the spectrum, and reversal on the first token as well as all 5.
- Config `configs/easyedit_rome_qwen2.5-1.5b.yaml`: their Qwen2.5-7B ROME file with only `model_name` changed (both models have 28 layers; layer 5, v_loss_layer 27, mom2_adjustment false).

Environment fixes needed for their pins on Windows: `pyarrow==14.0.2` (datasets 1.18.3 breaks on pyarrow 25), `numpy==1.23.5` (torch 2.0.1's wheel needs it; their file pins 1.22.1), plus `sniffio`, `openai`, `rouge` (imported but not pinned). torchvision 0.15.2 to stop timm pulling a newer torch.

Smoke test (1 dev case, cf4422 "Dudley Hardy lost their life at" -> Manila): rewrite_acc 0.00 -> 1.00, update norm 5.81 (rank one, so that is also its spectral norm). Our simplified edits were 3.0-4.4.

**Predictions (written before any results):**
1. Spectrum: the real ROME edit is the #1 singular component of the edited matrix in most cases (60-80%), with spectral norm at or above the original top singular value. Caveat: with mom2_adjustment false the update has the same form as ours, so a difference has to come from their v optimization, context-template averaging of the key, and layer 5 vs 4.
2. Best-q reversal (5 tokens back to base) on the 100 test cases: 40-70%, central guess 50%.
3. Of reversed cases, exactly base on all probes: under 20%, central guess 5%. Dropping the top component removes a mix of edit and original matrix, so expect inverse-like collateral changes rather than subtract-like exactness.

## 2026-11-01 (21:00): ICLR SVD reversal, first attempt, and why the 100-case run was held back

Added `revoke_mode="svd"` (drop the top-q singular components of the edited matrix, as in Youssef et al.'s `get_excl_approximation`; a test checks the reconstruction matches theirs). Built a 20-case dev set disjoint from the test set (`counterfact_dev20_seed1`) and swept q = 0..20 with the paper's criterion (prediction returns to the base prediction, 5 tokens).

**Result on our ROME-style edits:** reversal stays at 0-10% for every q (best q=16, 0.10), while the edit survives in 35-100% of cases. The paper reports 62.9% on Qwen2.5-7B.

**Diagnosis** (`scratch/diag_svd_spectrum.py`, 5 dev cases): our edits have spectral norm ~3.0-4.4, below the matrix's existing top singular values (7.87 down to 4.23 at #20). The edit doesn't sit in the top components: its best-aligned component is #5-#14 with weak alignment (0.06-0.42), and dropping the top 16 components removes only 39-93% of the edit (plus 16 components of the original matrix). Same with identity covariance.

**So this run doesn't test their method fairly.** SVD truncation assumes edits dominate the top of the spectrum. Real ROME edits apparently do; our simplified edits don't. Running 100 test cases now would produce a misleading "their method fails" claim. Held back.

**Next (fair test):** make genuine ROME edits with the EasyEdit code bundled in their repo (their Qwen2.5-7B config sets `mom2_adjustment: false`, so no Wikipedia covariance download), adapt the config to Qwen2.5-1.5B, then re-run the q sweep and the 100 cases through our harness. Also compare their first-token "reversal accuracy" with our stricter 5-token match.

**Prediction check:** the earlier prediction (SVD undo between subtract 0.86 and inverse 0.00) is untested. It was premised on edits the method can see.

## 2026-11-01 (landscape review and plan decision)

**Landscape review** (full write-up in the project document "Landscape Review: Who Else Is Working on Revocable Model Edits"):
- At least five 2025-26 papers reverse knowledge edits: Youssef et al. (ICLR 2026, SVD truncation, public code), Jiang et al. (Sept 2026, selective reversal), Caddeo et al. (July 2026, inverse edits), SoLA (Mar 2026, per-edit LoRA keys), and in-context edit reversal (NAACL 2025). Each covers one editor family and judges reversal mainly on the edited fact.
- Unlearning evaluation is further along on verification: hidden-state probes (Goel et al. 2026), relearning attacks, statistical tests against a noise floor (Google, AISTATS 2026), and meta-evaluation of metrics (OpenUnlearning). All transfer to edit undo.
- Commercial: Hirundo ($8M seed, June 2025) sells unlearning without published verification; Mem0 offers deletion but no proof of deletion. Nobody sells independent verification yet.
- Terminology: an ICML 2026 position paper asks work to name its guarantee and reference model. Ours: return to the base model on the probe set.

**Decision:** wait about a week before the first public write-up, and use it to run the ICLR SVD-truncation reversal from the authors' own code. A claim tested against others' implementations is much harder to dismiss, and it gives a natural reason to contact those authors. If the code won't run on the 3070 within about a week, publish without it and note it as next.

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

**Ops note:** cases 70-71 of the last variant slowed from ~25 s to many minutes because another application was holding GPU memory (7.66 / 8 GB VRAM in use, spilling to system RAM). Closing it restored normal speed. To add: a startup warning when other processes hold significant VRAM, and an ETA every 10 cases.

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
