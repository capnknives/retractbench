## 2026-11-02 (morning): real ROME edits from the authors' EasyEdit, setup and predictions

**Setup.** Their repo (github.com/paulyoussef/trace-and-reverse, commit d783bc1) is cloned to `D:\trace-and-reverse` with its own venv (Python 3.10, torch 2.0.1+cu118, transformers 4.46.2), because their EasyEdit pins an older transformers than ours. Editing and scoring are split:
- `scripts/easyedit_rome_export.py` (their venv) calls their `BaseEditor.edit` exactly as `reversing_single_edits.py` does, wraps their `execute_rome` to save each case's two ROME vectors, and checks the matrix is back to its original values after every case. It records their own `rewrite_acc` (their script skips edits below 1.0).
- `editors/precomputed.py` (`PrecomputedRomeEditor`) replays those updates in our harness with the existing restore / subtract / svd undo modes. Mechanics tests in `tests/test_precomputed_tiny.py`.
- `run_rome.py` and `sweep_svd_q.py` gained `--deltas` and `--dtype` (their edits are made on an fp32 model, so we score in fp32 too). The sweep now also reports where each edit sits in the spectrum, and reversal on the first token as well as all 5.
- Config `configs/easyedit_rome_qwen2.5-1.5b.yaml`: their Qwen2.5-7B ROME file with only `model_name` changed (both models have 28 layers; layer 5, v_loss_layer 27, mom2_adjustment false).

Environment fixes needed for their pins on Windows: `pyarrow==14.0.2` (datasets 1.18.3 breaks on pyarrow 25), `numpy==1.23.5` (torch 2.0.1's wheel needs it; their file pins 1.22.1), plus `sniffio`, `openai`, `rouge` (imported but not pinned). torchvision 0.15.2 to stop timm pulling a newer torch.

Smoke test (1 dev case, cf4422 "Dudley Hardy lost their life at" -> Manila): rewrite_acc 0.00 -> 1.00, update norm 5.81 (rank one, so that is also its spectral norm). Our simplified edits were 3.0-4.4.

**Predictions (written before any results; Claude's reasoning, Andy agreed):**
1. Spectrum: the real ROME edit is the #1 singular component of the edited matrix in most cases (60-80%), with spectral norm at or above the original top singular value. Caveat: with mom2_adjustment false the update has the same form as ours, so a difference has to come from their v optimization, context-template averaging of the key, and layer 5 vs 4.
2. Best-q reversal (5 tokens back to base) on the 100 test cases: 40-70%, central guess 50%.
3. Of reversed cases, exactly base on all probes: under 20%, central guess 5%. Dropping the top component removes a mix of edit and original matrix, so expect inverse-like collateral changes rather than subtract-like exactness.

