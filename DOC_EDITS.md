# Document edit history

Every edit Claude makes to a document outside this repo (Claude Docs, Google Drive) is logged here, newest first: the time, which document, what changed, and why. Use it to check or backtrack.

To undo:
- **Claude Docs** keep every revision. Give Claude the rev number and it can read that rev back or restore it.
- **Google Docs**: File → Version history.

## Documents

| Name | Where | ID / link |
| --- | --- | --- |
| Write-up draft, "Restoring the Fact Is Not Restoring the Model (draft)" | Claude Docs | https://claude.ai/artifact/9RGHHhmjeHEtuTPxwDwiC8 |
| Landscape Review: Who Else Is Working on Revocable Model Edits | Claude Docs | (id starts b13035b6) |
| retractbench Status Update — Nov 2, 2026 | Google Drive | 17pA5IAz… |
| retractbench Research Brief for Gemini — Nov 2, 2026 | Google Drive | 1PBdf_O2… |
| retractbench Plan Update + Gemini Report Triage — Nov 2, 2026 (13:00) | Google Drive | https://docs.google.com/document/d/1pu8ei4rRbP674P_2Wug7oOz2hQwoNiIBxiLuQmbBE9c |
| Master Plan v3, Overview (current) | Google Drive | not edited by Claude |

## 2026-11-02

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
