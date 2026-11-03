# Lab log

Dated entries, newest first. Failures and dead ends go in too.

## 2026-11-03 (11:15): Resumable export tested; cloud pipeline for Qwen2.5-7B (predictions)

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
