"""Cross-check equality.py against the authors' own package (model-equality-testing 0.0.2).

Skipped when the package isn't installed. The statistic must match theirs
exactly; permutation p-values use different random draws, so they only have to
agree within Monte Carlo error.
"""
import numpy as np
import pytest

met = pytest.importorskip("model_equality_testing")
from model_equality_testing.algorithm import run_two_sample_test  # noqa: E402
from model_equality_testing.distribution import CompletionSample  # noqa: E402
from model_equality_testing.tests import mmd_hamming  # noqa: E402

from retractbench.equality import two_sample_test  # noqa: E402


def _draw(rng, probs, n_per_prompt, L):
    prompts, comps = [], []
    for p, pr in enumerate(probs):
        for _ in range(n_per_prompt):
            prompts.append(p)
            comps.append(rng.choice(len(pr), size=L, p=pr))
    return np.array(prompts), np.array(comps)


@pytest.mark.parametrize("shift", [False, True])
def test_statistic_matches_package_exactly(shift):
    rng = np.random.default_rng(3)
    m = 6
    pa, ca = _draw(rng, [np.array([0.5, 0.3, 0.2])] * m, 10, 8)
    q = np.array([0.2, 0.3, 0.5]) if shift else np.array([0.5, 0.3, 0.2])
    pb, cb = _draw(rng, [q] * m, 10, 8)
    ours = two_sample_test(pa, ca, pb, cb, n_permutations=1)["mmd"]
    theirs = mmd_hamming(CompletionSample(prompts=pa, completions=ca, m=m),
                         CompletionSample(prompts=pb, completions=cb, m=m))
    assert ours == pytest.approx(float(theirs), rel=1e-9, abs=1e-12)


def test_pvalues_agree_within_monte_carlo_error():
    rng = np.random.default_rng(4)
    m = 6
    pa, ca = _draw(rng, [np.array([0.5, 0.3, 0.2])] * m, 10, 8)
    pb, cb = _draw(rng, [np.array([0.4, 0.3, 0.3])] * m, 10, 8)
    ours = two_sample_test(pa, ca, pb, cb, n_permutations=2000, seed=0)["p_value"]
    theirs, _ = run_two_sample_test(CompletionSample(prompts=pa, completions=ca, m=m),
                                    CompletionSample(prompts=pb, completions=cb, m=m),
                                    pvalue_type="permutation_pvalue", stat_type="mmd_hamming", b=2000)
    assert abs(ours - theirs) < 0.05, (ours, theirs)
