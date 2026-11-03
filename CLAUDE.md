# Notes for Claude

## What this project is
`retractbench` measures whether edits to a language model can be fully revoked. It is Richard Elliot's research project and public portfolio; the commit history and LOG.md are part of the deliverable.

## Rules
- Keep changes small, readable and reviewable; prefer clarity over cleverness, and document non-obvious PyTorch behaviour in the commit message.
- Never change metric definitions in `src/retractbench/harness.py` silently. Any change to how a metric is computed needs a LOG.md entry and an updated test in `tests/test_harness.py`.
- Every new editor gets a mechanics test on the tiny random model (see `tests/test_grace_tiny.py`) before it's used for real numbers.
- Don't hand-edit files in `results/`. Results come from runs only.
- No claims in README or write-ups that a run hasn't shown. In particular: revocation here undoes an edit; it does not remove anything the base model learned in pretraining.
- Before a new experiment, write the predictions in LOG.md as plain predictions, not attributed to a person.
- In anything public or professional (README, write-ups, emails, citation metadata), the author is Richard Elliot. No nickname.

## Layout
- `DOC_EDITS.md`: log of every edit Claude makes to documents outside the repo (Claude Docs, Google Drive). Add an entry for each edit, newest first.
- `src/retractbench/types.py`: `EditCase`, `CaseResult`, `Editor` protocol (pure Python)
- `src/retractbench/harness.py`: the protocol and metrics (pure Python)
- `src/retractbench/report.py`: case loading and result saving
- `src/retractbench/separability.py`: key-distance analysis without training (AUC, recall at a hard-negative budget)
- `src/retractbench/equality.py`: MMD two-sample test on sampled text (Gao et al.), pure Python
- `src/retractbench/gpu.py`: pre-run check that other programs aren't holding GPU memory
- `src/retractbench/editors/`: one module per method (`grace.py`, `rome.py`, `precomputed.py` replays edits exported from EasyEdit); these need torch
- `configs/`: hyperparameter files for the authors' EasyEdit (`easyedit_rome_qwen2.5-1.5b.yaml`)
- `data/easyedit_rome/`: exported EasyEdit edits (`dev20.pt`, `cf100.pt`)
- `scripts/`: experiment runners (`run_matched.py` for GRACE variants, `run_rome.py` for weight edits, `sweep_svd_q.py`, `run_stat_undo.py`), `easyedit_rome_export.py` (runs in the authors' venv), case builders, analyses (`rescore_leaks.py`)
- `cases/`: JSONL case files (`fictional_v0`, `counterfact_100_seed0`)
- `results/`: run outputs (JSON + Markdown); `results/logs/` holds console logs

## Environment
- Windows PC, RTX 3070 (8 GB). Project at `D:\retractbench`, venv at `D:\retractbench\.venv`.
- Keep model downloads off C: (set `HF_HOME=D:\hf-cache`).
- Second venv for the authors' code: `D:\trace-and-reverse\.venv` (Python 3.10, torch 2.0.1+cu118, transformers 4.46.2, pyarrow 14.0.2, numpy 1.23.5, torchvision 0.15.2). Never install its pins into our venv. Edits travel as `data/easyedit_rome/<tag>.pt`; replay with `--deltas ... --dtype float32`.
- EasyEdit ROME in fp32 uses ~7.7 of 8 GB VRAM, ~105 s per edit; nothing else on the GPU meanwhile.
- Always state the reversal criterion with a number: Youssef et al. score the next token only; ours is all generated tokens equal to base.

## Commands
- `.\.venv\Scripts\python.exe -m pytest`: all tests (torch tests skip if torch isn't installed)
- `.\.venv\Scripts\retractbench.exe run --model <hf id> --cases cases/fictional_v0.jsonl [--layer N --eps X]`
- `.\.venv\Scripts\python.exe scripts\run_rome.py --cases cases\counterfact_100_seed0.jsonl --tag cf100 --layers 4 --modes restore subtract inverse --covariance calibration`
- Long runs: launch in their own PowerShell window with output Tee'd to `results\logs\`, with nothing else holding GPU memory (another application holding VRAM slowed a run ~20x on 2026-11-01; `gpu.py` checks for this).
- Export EasyEdit edits (their venv): `cd D:\trace-and-reverse; .venv\Scripts\python.exe D:\retractbench\scripts\easyedit_rome_export.py --cases D:\retractbench\cases\counterfact_100_seed0.jsonl --tag cf100 --hparams D:\retractbench\configs\easyedit_rome_qwen2.5-1.5b.yaml`
- Score them (our venv): `.\.venv\Scripts\python.exe scripts\run_rome.py --cases cases\counterfact_100_seed0.jsonl --tag ee_cf100 --deltas data\easyedit_rome\cf100.pt --dtype float32 --modes restore subtract svd`
- Runs reset the model between cases by default (`isolate=True`). Only use `--no-isolate` to measure accumulated drift on purpose.

## Current phase
Preparing the first public write-up (target Nov 9–15, 2026): "restoring the fact is not restoring the model."
Before it goes out: run the ICLR 2026 SVD-truncation reversal (Youssef et al., authors' code) through the harness, so the claim is tested against others' own implementations, not only ours. If their code can't run here within about a week, the decision is to publish without it and note it as next.
Status 2026-11-02 16:45: all write-up runs done (LOG 13:00, 14:15, 15:25), draft checked by an independent reviewer (LOG 15:05). Decided: blog post + GitHub first (tagged release archived on Zenodo for a DOI), arXiv when an endorser is found; Result 2 leads; Youssef et al. get the draft 3-4 days before posting (proposed: email Nov 9, post Nov 12). Blog post drafted as a Claude Doc (LOG 16:30). Next: review the post, write the email to Youssef et al. External doc edits are logged in DOC_EDITS.md.
Status 2026-11-03 09:15: both truncation controls done (LOG 2026-11-02 17:20, 19:00); independent review applied (LOG 21:30); test set also run at q=10 with its control (LOG 2026-11-03 09:05). The post reports q=3 and q=10 side by side. Email to Youssef et al. drafted (Claude Doc), send Nov 9; post Nov 12.
Direction (LOG 17:50, Master Plan v4): research and open benchmark, not a startup. The contribution is the cross-method comparison of undo designs, not "SVD isn't exact". After the post, in order: MMD power calibration, GRACE rollback (EasyEdit), LoRA-per-edit, MEMIT batch-minus-one / AlphaEdit, a second model family at 1-3B. Measured wording in all write-ups; no "catastrophic" or "unprecedented".
See the Roadmap in README.md and the 2026-11-02 (17:50) entry in LOG.md.
