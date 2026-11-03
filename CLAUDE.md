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
- `configs/`: hyperparameter files for the authors' EasyEdit (`easyedit_rome_qwen2.5-1.5b.yaml`; `easyedit_rome_qwen2.5-7b.yaml` is the authors' file unchanged)
- `data/easyedit_rome/`: exported EasyEdit edits for 1.5B (`dev20.pt`, `cf100.pt`; not committed). The 7B edits (`dev20_7b.pt`, `cf100_7b.pt`) live on the Modal volume `retractbench-vol` under `data/easyedit_rome/`
- `labels/`: hand labels (`svd3_q3_cf100_leaks_labelled.json`, the 1.5B q=3 leak flags)
- `scripts/modal_app.py` + `scripts/modal/requirements_*.txt`: cloud runs (download, export, sweep, score, stat) for models that don't fit the local GPU
- `scripts/`: experiment runners (`run_matched.py` for GRACE variants, `run_rome.py` for weight edits, `sweep_svd_q.py`, `run_stat_undo.py`), `easyedit_rome_export.py` (runs in the authors' venv), case builders, analyses (`rescore_leaks.py`)
- `cases/`: JSONL case files (`fictional_v0`, `counterfact_100_seed0`)
- `results/`: run outputs (JSON + Markdown); `results/logs/` holds console logs

## Environment
- Windows PC, RTX 3070 (8 GB). Project at `D:\retractbench`, venv at `D:\retractbench\.venv`.
- Keep model downloads off C: (set `HF_HOME=D:\hf-cache`).
- Second venv for the authors' code: `D:\trace-and-reverse\.venv` (Python 3.10, torch 2.0.1+cu118, transformers 4.46.2, pyarrow 14.0.2, numpy 1.23.5, torchvision 0.15.2). Never install its pins into our venv. Edits travel as `data/easyedit_rome/<tag>.pt`; replay with `--deltas ... --dtype float32`.
- EasyEdit ROME in fp32 uses ~7.7 of 8 GB VRAM, ~105 s per edit; nothing else on the GPU meanwhile.
- Cloud: Modal client in its own venv `D:\modal-venv` (token in `%USERPROFILE%\.modal.toml`). Set `MODAL_IMAGE_BUILDER_VERSION=2025.06` (the authors' pins need Python 3.10) and always `modal run --detach`, so closing a window doesn't stop the job. Don't launch more than one job every ~20 s (Modal's app-create rate limit). The account has $30/month free credit; the Nov 3 7B runs used about half. Copy results with `modal volume get retractbench-vol rb/results/ <dir>`; run files then go into `results/` unchanged.
- Always state the reversal criterion with a number: Youssef et al. score the next token only; ours is all generated tokens equal to base.

## Commands
- `.\.venv\Scripts\python.exe -m pytest`: all tests (torch tests skip if torch isn't installed)
- `.\.venv\Scripts\retractbench.exe run --model <hf id> --cases cases/fictional_v0.jsonl [--layer N --eps X]`
- `.\.venv\Scripts\python.exe scripts\run_rome.py --cases cases\counterfact_100_seed0.jsonl --tag cf100 --layers 4 --modes restore subtract inverse --covariance calibration`
- Long runs: launch in their own PowerShell window with output Tee'd to `results\logs\`, with nothing else holding GPU memory (another application holding VRAM slowed a run ~20x on 2026-11-01; `gpu.py` checks for this).
- Export EasyEdit edits (their venv): `cd D:\trace-and-reverse; .venv\Scripts\python.exe D:\retractbench\scripts\easyedit_rome_export.py --cases D:\retractbench\cases\counterfact_100_seed0.jsonl --tag cf100 --hparams D:\retractbench\configs\easyedit_rome_qwen2.5-1.5b.yaml`
- Score them (our venv): `.\.venv\Scripts\python.exe scripts\run_rome.py --cases cases\counterfact_100_seed0.jsonl --tag ee_cf100 --deltas data\easyedit_rome\cf100.pt --dtype float32 --modes restore subtract svd`
- Control for an approximate undo: the same command with `--null-edit` (zero updates, so the undo acts on the unedited model), then `scripts/compare_null_svd.py <run> <control> <out>`.
- Runs reset the model between cases by default (`isolate=True`). Only use `--no-isolate` to measure accumulated drift on purpose.

## Current phase
First public write-up: preview email to Youssef et al. on Nov 9, blog post + tagged release (Zenodo DOI) on Nov 12, 2026. arXiv when an endorser is found.
Status 2026-11-03 15:15: all write-up runs are done on both models (LOG 2026-11-03 13:30 and 15:10 for 7B; 2026-11-02 entries for 1.5B). The blog post (Claude Doc, see DOC_EDITS.md) was restructured around the 7B result. Its framing: on the authors' model at the dev-chosen q=15, SVD undo gets close but not exact (leak 3% vs control 0.7%, MMD 6/100 = null, 0/100 exact, ES 0.30 vs 0.17); far off on 1.5B (q=3: leak 43%, MMD 45/100); only restore/subtract are exact. The email draft and podcast brief match. The second independent check of the restructured post is done (LOG 2026-11-03 15:32; no wrong numbers, wording fixed). Remaining before launch: the author's read-through, fixing the Drive Part 3 podcast brief by hand, the Zenodo link, sending the email, publishing.
Direction (LOG 2026-11-02 17:50, Master Plan v4): research and open benchmark, not a startup. The contribution is a return-to-model standard with controls, and a cross-method comparison of undo designs. After the post, in order: MMD power calibration, GRACE rollback (EasyEdit), LoRA-per-edit, MEMIT batch-minus-one / AlphaEdit, a second model family. Measured wording in all write-ups; no "catastrophic" or "unprecedented".
See the Roadmap in README.md.
