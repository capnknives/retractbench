# Notes for Claude

## What this project is
`retractbench` measures whether edits to a language model can be fully revoked. It is Andy's research project and public portfolio; the commit history and LOG.md are part of the deliverable.

## Rules
- Andy must be able to explain every line. Prefer small, readable changes over clever ones, and explain any non-obvious PyTorch behavior in the PR or commit message.
- Never change metric definitions in `src/retractbench/harness.py` silently. Any change to how a metric is computed needs a LOG.md entry and an updated test in `tests/test_harness.py`.
- Every new editor gets a mechanics test on the tiny random model (see `tests/test_grace_tiny.py`) before it's used for real numbers.
- Don't hand-edit files in `results/`. Results come from runs only.
- No claims in README or write-ups that a run hasn't shown. In particular: revocation here undoes an edit; it does not remove anything the base model learned in pretraining.
- Ask Andy to predict results before a new experiment and record the prediction in LOG.md.

## Layout
- `src/retractbench/types.py`: `EditCase`, `CaseResult`, `Editor` protocol (pure Python)
- `src/retractbench/harness.py`: the protocol and metrics (pure Python)
- `src/retractbench/report.py`: case loading and result saving
- `src/retractbench/separability.py`: key-distance analysis without training (AUC, recall at a hard-negative budget)
- `src/retractbench/gpu.py`: pre-run check that other programs aren't holding GPU memory
- `src/retractbench/editors/`: one module per method (`grace.py`, `rome.py`); these need torch
- `scripts/`: experiment runners (`run_matched.py` for GRACE variants, `run_rome.py` for weight edits), case builders, analyses
- `cases/`: JSONL case files (`fictional_v0`, `counterfact_100_seed0`)
- `results/`: run outputs (JSON + Markdown); `results/logs/` holds console logs

## Environment
- Windows PC, RTX 3070 (8 GB). Project at `D:\retractbench`, venv at `D:\retractbench\.venv`.
- Keep model downloads off C: (set `HF_HOME=D:\hf-cache`).

## Commands
- `.\.venv\Scripts\python.exe -m pytest`: all tests (torch tests skip if torch isn't installed)
- `.\.venv\Scripts\retractbench.exe run --model <hf id> --cases cases/fictional_v0.jsonl [--layer N --eps X]`
- `.\.venv\Scripts\python.exe scripts\run_rome.py --cases cases\counterfact_100_seed0.jsonl --tag cf100 --layers 4 --modes restore subtract inverse --covariance calibration`
- Long runs: launch in their own PowerShell window with output Tee'd to `results\logs\`, and close games first (a game holding VRAM slowed a run ~20x on 2026-11-01).
- Runs reset the model between cases by default (`isolate=True`). Only use `--no-isolate` to measure accumulated drift on purpose.

## Current phase
Preparing the first public write-up (target Nov 9–15, 2026): "restoring the fact is not restoring the model."
Before it goes out: run the ICLR 2026 SVD-truncation reversal (Youssef et al., authors' code) through the harness, so the claim is tested against others' own implementations, not only ours. If their code can't run here within about a week, Andy has decided to publish without it and note it as next.
See the Roadmap in README.md and the 2026-11-01 (landscape review) entry in LOG.md.
