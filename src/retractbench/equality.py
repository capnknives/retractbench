"""Statistical test: is the model after undo the same *distribution* as the base model?

Exact greedy matching (harness.revocation_exact) asks whether the most likely
answer to each probe came back. A model can pass that and still have a shifted
output distribution, or fail it on a near-tie while being almost unchanged.
This module asks the distributional question with the two-sample test of

    Gao, Liang & Guestrin, "Model Equality Testing: Which Model Is This API
    Serving?", ICLR 2025 (arXiv:2410.20247), Sections 2-3 and Appendix A.2.

Implemented from the paper's equations (pure numpy), not their package:
  - samples are (prompt id, completion) pairs, completions as token-id arrays
    right-padded to a fixed length L with PAD;
  - kernel  k(z, z') = 1{x = x'} * sum_i 1{y_i = y'_i}   (their eq. 7 inside
    the prompt indicator), divided by L so it is unit-norm;
  - statistic: the MMD estimator as computed in the authors' package (mean over\n    same-prompt pairs; see mmd_from_gram for how this differs from eq. 4);
  - p-value: the permutation procedure of their Algorithm 2.
H0 is "same distribution over completions for these prompts". The Hamming MMD is
a pseudo-metric (their A.1): it can miss differences that leave every
position's marginal distribution unchanged, so "not rejected" is not proof of
equality, only failure to detect a difference at this sample size.
"""
from __future__ import annotations

import numpy as np

PAD = -1


def pad_completions(completions: list[list[int]], length: int) -> np.ndarray:
    """Right-pad (or truncate) token-id lists to `length` with PAD."""
    out = np.full((len(completions), length), PAD, dtype=np.int64)
    for i, c in enumerate(completions):
        c = list(c)[:length]
        out[i, : len(c)] = c
    return out


def hamming_gram(prompts: np.ndarray, completions: np.ndarray) -> np.ndarray:
    """Kernel matrix K[i, j] = 1{p_i = p_j} * (# positions where completions agree) / L.

    Padding counts as a token, as in the paper: two completions that both
    stopped before position i agree there."""
    n, L = completions.shape
    same_prompt = prompts[:, None] == prompts[None, :]
    agree = np.zeros((n, n), dtype=np.float64)
    for i in range(L):  # loop over positions keeps memory at n x n
        col = completions[:, i]
        agree += col[:, None] == col[None, :]
    return same_prompt * agree / L


def mmd_from_gram(K: np.ndarray, in_a: np.ndarray, same_prompt: np.ndarray) -> float:
    """MMD estimate for sample A = rows with in_a True, B = the rest.

    Each of the three terms is the mean kernel value over pairs that share a
    prompt (pairs with different prompts have kernel 0 and are not counted),
    and within-sample terms skip a sample paired with itself. This follows the
    authors' package (model_equality_testing.tests._mmd), which produced their
    reported results. The paper's eq. 4 instead divides by all pairs, N(N-1) and
    N^2; with several prompts the two are not proportional, so p-values can
    differ slightly. Either way the permutation test is valid; we match the
    package so results are comparable with theirs."""
    a, b = np.flatnonzero(in_a), np.flatnonzero(~in_a)

    def mean_same(rows, cols, within):
        k, s = K[np.ix_(rows, cols)], same_prompt[np.ix_(rows, cols)]
        total, count = k.sum(), s.sum()
        if within:
            total, count = total - np.trace(k), count - len(rows)
        return total / count if count > 0 else 0.0

    return float(mean_same(a, a, True) + mean_same(b, b, True) - 2.0 * mean_same(a, b, False))


def two_sample_test(prompts_a, completions_a, prompts_b, completions_b,
                    n_permutations: int = 1000, seed: int = 0) -> dict:
    """Hamming-MMD two-sample test with a permutation p-value (their Algorithm 2).

    p = (1 + #{permuted stat >= observed}) / (1 + B): the "+1" counts the
    observed split as one of the permutations, which keeps the test's
    false-positive rate at or below alpha (a common, slightly conservative
    variant of the plain proportion in Algorithm 2)."""
    prompts = np.concatenate([np.asarray(prompts_a), np.asarray(prompts_b)])
    comps = np.concatenate([np.asarray(completions_a), np.asarray(completions_b)])
    if comps.ndim != 2:
        raise ValueError("completions must be padded to a 2-D array (see pad_completions)")
    in_a = np.zeros(len(prompts), dtype=bool)
    in_a[: len(prompts_a)] = True
    K = hamming_gram(prompts, comps)
    same = prompts[:, None] == prompts[None, :]
    observed = mmd_from_gram(K, in_a, same)
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_permutations):
        count += mmd_from_gram(K, rng.permutation(in_a), same) >= observed
    return {"mmd": observed, "p_value": (1 + count) / (1 + n_permutations),
            "n_a": int(in_a.sum()), "n_b": int((~in_a).sum()), "n_permutations": n_permutations}
