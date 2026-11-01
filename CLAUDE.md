# Notes for Claude

## What this project is
`revbench` measures whether edits to a language model can be fully revoked. It is Andy's research project and public portfolio; the commit history and LOG.md are part of the deliverable.

## Rules
- Andy must be able to explain every line. Prefer small, readable changes over clever ones, and explain any non-obvious PyTorch behavior in the PR or commit message.
- Never change metric definitions in `src/revbench/harness.py` silently. Any change to how a metric is computed needs a LOG.md entry and an updated test in `tests/test_harness.py`.
- Every new editor gets a mechanics test on the tiny random model (see `tests/test_grace_tiny.py`) before it's used for real numbers.
- Don't hand-edit files in `results/`. Results come from runs only.
- No claims in README or write-ups that a run hasn't shown. In particular: revocation here undoes an edit; it does not remove anything the base model learned in pretraining.
- Ask Andy to predict results before a new experiment and record the prediction in LOG.md.

## Layout
- `src/revbench/types.py`: `EditCase`, `CaseResult`, `Editor` protocol (pure Python)
- `src/revbench/harness.py`: the protocol and metrics (pure Python)
- `src/revbench/report.py`: case loading and result saving
- `src/revbench/editors/`: one module per method; these need torch
- `cases/`: JSONL case files
- `results/`: run outputs (JSON + Markdown)

## Environment
- Windows PC, RTX 3070 (8 GB). Project at `D:\revbench`, venv at `D:\revbench\.venv`.
- Keep model downloads off C: (set `HF_HOME=D:\hf-cache`).

## Commands
- `.\.venv\Scripts\python.exe -m pytest`: all tests (torch tests skip if torch isn't installed)
- `.\.venv\Scripts\revbench.exe run --model <hf id> --cases cases/fictional_v0.jsonl [--layer N --eps X]`

## Current phase
Phase 1: reproduce GRACE, validate the harness on a real 1B model, then compare against EasyEdit.
