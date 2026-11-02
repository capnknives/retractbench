## 2026-11-02 (09:00): statistical undo test, cross-checked against the authors' package

New `src/retractbench/equality.py`: the Hamming-MMD two-sample test of Gao, Liang & Guestrin, "Model Equality Testing" (ICLR 2025, arXiv:2410.20247), plus `scripts/run_stat_undo.py`, which samples every probe at temperature 1 (10 samples per prompt, 20 tokens) from the base model twice (the base-vs-base null) and once after each undo, and tests base vs post-undo. `restore` is the control and should reject at about alpha. This is a new metric module; nothing in harness.py changed.

**A discrepancy found while cross-checking.** The paper's eq. 4 averages kernel values over all sample pairs (N(N-1), N^2). Their package (`model_equality_testing.tests._mmd`) averages only over pairs that share a prompt. With several prompts these are not proportional. Their reported results come from the package, so equality.py follows the package (the docstring says so). Both give valid permutation tests.

**Cross-check** (`tests/test_equality_crosscheck.py`, needs `model-equality-testing==0.0.2`, MIT, installed with Andy's OK): our statistic equals theirs to 1e-9 on multi-prompt data with and without a shift; permutation p-values agree within 0.05 at 2000 permutations. Also tested: the kernel formula by hand, false-positive rate near alpha on equal distributions, and detection of a clear shift.

