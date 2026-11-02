"""Hamming-MMD two-sample test (equality.py): formulas and error rates on synthetic data."""
import numpy as np
import pytest

from retractbench.equality import (PAD, hamming_gram, mmd_from_gram, pad_completions,
                                   two_sample_test)


def test_pad_completions_pads_and_truncates():
    out = pad_completions([[5, 6], [1, 2, 3, 4]], length=3)
    assert out.tolist() == [[5, 6, PAD], [1, 2, 3]]


def test_kernel_is_zero_across_prompts_and_counts_agreeing_positions():
    prompts = np.array([0, 0, 1])
    comps = np.array([[1, 2, 3, 4], [1, 9, 3, 9], [1, 2, 3, 4]])
    K = hamming_gram(prompts, comps)
    assert K[0, 1] == pytest.approx(2 / 4)   # positions 0 and 2 agree
    assert K[0, 2] == 0.0                    # different prompts
    assert np.allclose(np.diag(K), 1.0)      # unit norm


def test_mmd_matches_eq4_by_hand():
    # one prompt, completions of length 1: kernel is just "same token"
    prompts = np.zeros(4, dtype=int)
    comps = np.array([[1], [1], [2], [2]])
    K = hamming_gram(prompts, comps)
    in_a = np.array([True, True, False, False])
    # within A: one off-diagonal pair agrees (both 1) -> 2/(2*1) = 1; same for B; cross: all 0
    assert mmd_from_gram(K, in_a, prompts[:, None] == prompts[None, :]) == pytest.approx(1 + 1 - 0)


def _draw(rng, probs, n_per_prompt, L):
    prompts, comps = [], []
    for p, pr in enumerate(probs):
        for _ in range(n_per_prompt):
            prompts.append(p)
            comps.append(rng.choice(len(pr), size=L, p=pr))
    return np.array(prompts), np.array(comps)


def test_false_positive_rate_is_near_alpha_when_distributions_are_equal():
    rng = np.random.default_rng(1)
    probs = [np.array([0.5, 0.3, 0.2])] * 5
    rejections = 0
    trials = 60
    for t in range(trials):
        pa, ca = _draw(rng, probs, 10, 6)
        pb, cb = _draw(rng, probs, 10, 6)
        rejections += two_sample_test(pa, ca, pb, cb, n_permutations=99, seed=t)["p_value"] < 0.05
    assert rejections / trials <= 0.15   # alpha = 0.05 plus Monte Carlo slack for 60 trials


def test_detects_a_clear_shift():
    rng = np.random.default_rng(2)
    pa, ca = _draw(rng, [np.array([0.8, 0.1, 0.1])] * 5, 10, 6)
    pb, cb = _draw(rng, [np.array([0.1, 0.1, 0.8])] * 5, 10, 6)
    assert two_sample_test(pa, ca, pb, cb, n_permutations=199)["p_value"] < 0.01
