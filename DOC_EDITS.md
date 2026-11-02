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
| Landscape Review: Who Else Is Working on Revocable Model Edits | Claude Docs | (id starts b13035b6) |
| retractbench Status Update — Nov 2, 2026 | Google Drive | 17pA5IAz… |
| retractbench Research Brief for Gemini — Nov 2, 2026 | Google Drive | 1PBdf_O2… |
| retractbench Plan Update + Gemini Report Triage — Nov 2, 2026 (13:00) | Google Drive | https://docs.google.com/document/d/1pu8ei4rRbP674P_2Wug7oOz2hQwoNiIBxiLuQmbBE9c |
| retractbench Master Plan v4: Research Track (current) | Google Drive | https://docs.google.com/document/d/1vY31Wflwgq_InyALWdeQOsCD6Scj0ymjtT6Q6hHguTA |
| AI Startup Master Plan v3 (superseded, kept for reference) | Google Drive | not edited by Claude |

## 2026-11-02

- **17:50, Master Plan v4 (Google Drive): created.** Replaces v3 (unchanged). Research track instead of startup framing; status table with the null-edit control; experiment order after the post (MMD power, GRACE rollback, LoRA-per-edit, MEMIT/AlphaEdit, second model family); SPAR/MATS applications. See LOG 17:50.
- **17:23, blog post draft (Claude Docs): rev 11 → 17.** Revised for the null-edit control (LOG 17:20). The TL;DR now leads with the leak and ES, and adds a bullet saying truncation cannot restore the model by design. The test-set table gains an ES column and a control row. The paragraph under it explains how to read the control. The ES paragraph gives the control's 0.22. The MMD paragraph is marked as confounded until the control is sampled.
- **17:22, write-up draft (Claude Docs): rev 30 → 32.** Summary bullet: the 1/100 figure now has the control's 0/100 beside it, and the leak has the control's 0.3%.
- **17:05, blog post draft (Claude Docs): rev 10 → 11.** "What does work" explains the 86% (simplified editor) vs 100% (genuine ROME, fp32) subtract results.
- **16:45, blog post draft (Claude Docs): created, rev 1 → 10.** Outline, then one section per revision: TL;DR, the method, scoring, results, leftovers, what works, limitations, code and sources. There were three wording fixes ("nearly the whole effect" → "the gap is large"; "a floor" → "likely undercounts"; run time). See LOG 16:30.
- **16:40, write-up draft (Claude Docs): rev 29 → 30.** Result 2 "Criterion matters" now quotes Youssef et al. Sec. 5.3: "more effective in removing the edit than in recovering the original object".
- **15:45, write-up draft (Claude Docs): rev 24 → 29** (one batch of 8 changes). Two decisions recorded and ticked: Result 2 leads, and Youssef et al. are contacted 3–4 days before posting. The Sec. 5.3 check is ticked. In Sources, the overstated Youssef line now gives their KL figure. The heading "Decisions for Andy" is renamed "Decisions". See LOG 15:45.
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
