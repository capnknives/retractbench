# Document edit history

Every edit Claude makes to a document outside this repo (Claude Docs, Google Drive) is logged here, newest first: the time, which document, what changed, and why. Use it to check or backtrack.

To undo:
- **Claude Docs** keep every revision. Give Claude the rev number and it can read that rev back or restore it.
- **Google Docs**: File → Version history.

## Documents

| Name | Where | ID / link |
| --- | --- | --- |
| Write-up draft, "Restoring the Fact Is Not Restoring the Model (draft)" | Claude Docs | https://claude.ai/artifact/9RGHHhmjeHEtuTPxwDwiC8 |
| Blog post draft, "The Fact Comes Back, the Model Doesn't" | Claude Docs | https://claude.ai/artifact/E3CacZR67ds4BBjfA5gd8x |
| Email to Youssef et al. (draft, send Nov 9) | Claude Docs | https://claude.ai/artifact/Po6Zy9DFNbfT1SeCShZUau |
| retractbench Podcast Part 2 Brief | Claude Docs | https://claude.ai/artifact/GUeF3uPe25b4BGFf6De9Z7 |
| Landscape Review: Who Else Is Working on Revocable Model Edits | Claude Docs | (id starts b13035b6) |
| retractbench Status Update — Nov 2, 2026 | Google Drive | 17pA5IAz… |
| retractbench Research Brief for Gemini — Nov 2, 2026 | Google Drive | 1PBdf_O2… |
| retractbench Plan Update + Gemini Report Triage — Nov 2, 2026 (13:00) | Google Drive | https://docs.google.com/document/d/1pu8ei4rRbP674P_2Wug7oOz2hQwoNiIBxiLuQmbBE9c |
| retractbench Master Plan v4: Research Track (current) | Google Drive | https://docs.google.com/document/d/1vY31Wflwgq_InyALWdeQOsCD6Scj0ymjtT6Q6hHguTA |
| AI Startup Master Plan v3 (superseded, kept for reference) | Google Drive | not edited by Claude |

## 2026-11-03

- **15:14, podcast brief (Claude Docs): rev 10 → 11.** The story paragraph now covers the 7B step. The "What survived the control" section is replaced by "Then the authors' own model". The next-experiments list drops the completed items. The numbers table now has both models and their controls. A "don't say 'the edit usually survives'" line is added.
- **15:13, email draft (Claude Docs): rev 7 → 10.** The bullets now lead with the 7B replication (70% vs 62.9%), the q=15 result with its control, and the 1.5B contrast. The subject says "Qwen2.5-7B and 1.5B". The note points to LOG 13:30 and 15:10.
- **15:12, blog post draft (Claude Docs): rev 48 → 56.** Restructured around the 7B result (LOG 13:30, 15:10). Everything below the byline was replaced (the earlier version is recoverable at rev 48). New sections: TL;DR, method (both models, edit side effects), scoring (with the control), results on 7B, results on 1.5B, what the undo leaves behind, what works, limitations (including the missing pre-run predictions for the 7B MMD test), code and sources. Two follow-up wording fixes: the 7B MMD was run for restore only; truncation damage on 7B vs 1.5B is 38% vs 40%.
- **09:35, email draft (rev 6 → 7) and podcast brief (rev 9 → 10), Claude Docs.** Author name changed from Richard "Andy" Elliot to Richard Elliot (the author's decision: no nickname in public or professional text). The blog post and the technical draft had no nickname to change.
- **09:15, podcast brief (Claude Docs): rev 8 → 9.** The numbers section adds the q=10 leak (10%, control 1%) and preference (41, control 21).
- **09:15, email draft (Claude Docs): rev 3 → 6.** The author's edits at rev 2-3 (sign-off on one line, Maestro removed) were kept. Bullet 2 adds the q=10 figures; bullet 3 says truncation changes probes at both settings; the note now says the numbers include q=10.
- **09:10, blog post draft (Claude Docs): rev 38 → 48.** Reports both test-set settings (LOG 09:05). The TL;DR is rewritten as "the edit can survive, depending on the setting" and "no setting gives the model back" (40% / 49% of probes changed by truncation alone). The test-set table adds q=10 and control q=10 rows. Q=10 sentences are added under the table and in the ES paragraph. The hand labels are marked as q=3. The Limitations bullet becomes "Two settings on the test set".
- **08:10, blog post draft (Claude Docs): rev 36 → 38.** The Data bullet now reports the edits' own side effects (125/300 unrelated, 327/500 look-alike answers changed) and the update-norm range. The first wording said "each one changed" and was fixed to "across the 100 edits" in rev 38. See LOG 08:10.
- **07:40, podcast brief (Claude Docs): created.** "retractbench Podcast Part 2 Brief", https://claude.ai/artifact/GUeF3uPe25b4BGFf6De9Z7: background for an AI podcast host, with the numbers quoted with their settings and a "don't say" list. It contains no numbers that are not in the blog post.

## 2026-11-02

- **21:30, email draft (Claude Docs): created.** "Email to Youssef et al. (draft, send Nov 9)", https://claude.ai/artifact/Po6Zy9DFNbfT1SeCShZUau. The numbers name their q settings, per the review (LOG 21:30).
- **21:30, blog post draft (Claude Docs): rev 20 → 36.** Applied the independent review's fixes (LOG 21:30): q settings named in the TL;DR; "by design" narrowed to "at this setting"; MMD overlap caveat; definitions of leak and ES; dev-table definitions note; README claim replaced with LOG.md; edits-not-committed note; run times; control CIs; a new Limitations bullet on the single q=3 operating point; the labelled leak file named.
- **19:10, blog post draft (Claude Docs): rev 17 → 20.** MMD section: added a control row (8 of 100, CI 4–15%), and replaced the "confounded" caveat with the control result (LOG 19:00). The section intro now says each check is read against the control.
- **17:50, Master Plan v4 (Google Drive): created.** Replaces v3 (unchanged). Research track instead of startup framing; status table with the null-edit control; experiment order after the post (MMD power, GRACE rollback, LoRA-per-edit, MEMIT/AlphaEdit, second model family); SPAR/MATS applications. See LOG 17:50.
- **17:23, blog post draft (Claude Docs): rev 11 → 17.** Revised for the null-edit control (LOG 17:20). The TL;DR now leads with the leak and ES, and adds a bullet saying truncation cannot restore the model by design. The test-set table gains an ES column and a control row. The paragraph under it explains how to read the control. The ES paragraph gives the control's 0.22. The MMD paragraph is marked as confounded until the control is sampled.
- **17:22, write-up draft (Claude Docs): rev 30 → 32.** Summary bullet: the 1/100 figure now has the control's 0/100 beside it, and the leak has the control's 0.3%.
- **17:05, blog post draft (Claude Docs): rev 10 → 11.** "What does work" explains the 86% (simplified editor) vs 100% (genuine ROME, fp32) subtract results.
- **16:45, blog post draft (Claude Docs): created, rev 1 → 10.** Outline, then one section per revision: TL;DR, the method, scoring, results, leftovers, what works, limitations, code and sources. There were three wording fixes ("nearly the whole effect" → "the gap is large"; "a floor" → "likely undercounts"; run time). See LOG 16:30.
- **16:40, write-up draft (Claude Docs): rev 29 → 30.** Result 2 "Criterion matters" now quotes Youssef et al. Sec. 5.3: "more effective in removing the edit than in recovering the original object".
- **15:45, write-up draft (Claude Docs): rev 24 → 29** (one batch of 8 changes). Two decisions recorded and ticked: Result 2 leads, and Youssef et al. are contacted 3–4 days before posting. The Sec. 5.3 check is ticked. In Sources, the overstated Youssef line now gives their KL figure. The decisions heading is renamed "Decisions". See LOG 15:45.
- **15:20, write-up draft (Claude Docs): rev 20 → 24** (one batch of 4 changes, counted as 4 revs). The reviewer's wording fixes: "CounterFact's probability scores" instead of "Caddeo's measure"; the "most lenient criterion" claim marked indicative; ES numbers stated instead of "doesn't pass".
- **15:30, write-up draft (Claude Docs): rev 19 → 20.** Added the Caddeo-measure table to Result 2 and a summary bullet (LOG 15:25). Intro no longer mentions [pending] numbers. Caddeo-metrics item ticked.
- **15:00, Plan Update doc (Drive): description set.** Added a correction notice: the test runs used 8 greedy tokens, not 5, and the leak rate is 130 of 300 target probes. The body text still says 5. It will be fixed in place by browser once that works (see LOG 15:05).
- **14:55, write-up draft (Claude Docs): rev 18 → 19.** Applied the independent checker's corrections (LOG 15:05):
  - 8-token window
  - 300-probe leak denominator
  - Result 1 subtract row (0.02 / 0.01)
  - spectrum claims
  - Youssef and Caddeo quotes
  - "consistent with" wording, with CIs
  - Jiang Table 5 reframed
  - NAACL venue dropped
  - Gao wording
  - open items ticked
- **14:20, write-up draft: rev 17 → 18.** Result 3 table and text filled; SVD leak paragraph from the hand labels; summary bullet on sampled outputs; distributional-test item ticked.
- **13:00, write-up draft: rev 16 → 17.**
  - Intro now says blog post first.
  - Summary and Result 2 got the test-set numbers.
  - Caddeo reframed fairly.
  - Scoring-criteria paragraph added to Related work.
  - Caveats updated.
  - Open items and decisions updated: venue decided; endorser, Caddeo-metrics and Jiang-reading items added.
- **13:00, Drive: created** "retractbench Plan Update + Gemini Report Triage — Nov 2, 2026 (13:00)".
- **Earlier on Nov 2 (before this file existed):**
  - Drive: created "Status Update — Nov 2" and "Research Brief for Gemini — Nov 2".
  - Landscape Review: added "Regulation and buyer demand" section.
  - Write-up draft: created and filled.
