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

