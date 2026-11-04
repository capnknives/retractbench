"""Graded divergence (divergence.py): the KL arithmetic, and mechanics on the tiny random model."""
import math

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")

from retractbench.divergence import (case_divergence, kl_per_position, probes_by_type,  # noqa: E402
                                     top2_gap)
from retractbench.editors.precomputed import PrecomputedRomeEditor  # noqa: E402
from test_grace_tiny import CASE  # noqa: E402
from test_precomputed_tiny import tiny_with_update  # noqa: E402,F401  (fixture)


def logp(*rows):
    return torch.log(torch.tensor(rows, dtype=torch.float64))


def test_kl_of_identical_distributions_is_zero():
    a = torch.log_softmax(torch.randn(5, 11, generator=torch.Generator().manual_seed(0)), -1)
    assert torch.all(kl_per_position(a, a) == 0)


def test_kl_matches_hand_computation_and_direction():
    p, q = logp([0.5, 0.5]), logp([0.9, 0.1])
    expected_pq = 0.5 * math.log(0.5 / 0.9) + 0.5 * math.log(0.5 / 0.1)
    expected_qp = 0.9 * math.log(0.9 / 0.5) + 0.1 * math.log(0.1 / 0.5)
    assert kl_per_position(p, q).item() == pytest.approx(expected_pq)
    assert kl_per_position(q, p).item() == pytest.approx(expected_qp)   # KL is not symmetric: base first


def test_kl_is_nonnegative_on_random_rows():
    g = torch.Generator().manual_seed(1)
    a = torch.log_softmax(torch.randn(50, 20, generator=g), -1)
    b = torch.log_softmax(torch.randn(50, 20, generator=g), -1)
    assert torch.all(kl_per_position(a, b) >= 0)


def test_top2_gap():
    gap = top2_gap(logp([0.6, 0.3, 0.1], [0.4, 0.4, 0.2]))
    assert gap[0].item() == pytest.approx(math.log(2))
    assert gap[1].item() == pytest.approx(0.0)


def test_probe_types_cover_all_eleven_kinds():
    by = probes_by_type(CASE)
    assert sum(len(v) for v in by.values()) == 1 + len(CASE.paraphrases) + len(CASE.unrelated) + len(CASE.hard_negatives)


def test_case_divergence_restore_zero_edit_and_svd_positive(tiny_with_update):  # noqa: F811
    model, tok, dW = tiny_with_update
    ed = PrecomputedRomeEditor(model, tok, {CASE.id: dW}, layer=1, revoke_mode="restore")
    try:
        W0 = ed.W.detach().clone()
        r = case_divergence(ed, CASE, [("restore", "restore", 0), ("subtract", "subtract", 0),
                                       ("svd1", "svd", 1)], max_new_tokens=3)
        assert torch.equal(ed.W, W0)                      # reset after every condition
        cond = r["conditions"]
        assert set(cond) == {"edited", "restore", "subtract", "svd1"}
        prompts = list(r["base"])
        assert all(cond["restore"][p]["kl_mean"] == 0.0 for p in prompts)        # bitwise the base matrix
        # subtract leaves float32 residue (~1e-7 in the weights), so its KL is tiny but not 0
        sub = max(cond["subtract"][p]["kl_mean"] for p in prompts)
        assert sub < 1e-6
        assert cond["edited"][CASE.prompt]["kl_first"] > 1e-3                    # the edit moved the prompt
        assert max(cond["svd1"][p]["kl_mean"] for p in prompts) > 10 * sub       # truncation changes more
        for p in prompts:
            n = r["base"][p]["n_tokens"]
            assert len(cond["svd1"][p]["kl"]) == n and len(r["base"][p]["top2_gap"]) == n
    finally:
        ed.close()


def test_null_edit_leaves_edited_equal_to_base(tiny_with_update):  # noqa: F811
    model, tok, dW = tiny_with_update
    ed = PrecomputedRomeEditor(model, tok, {CASE.id: torch.zeros_like(dW)}, layer=1, source="null-edit")
    try:
        r = case_divergence(ed, CASE, [("svd1", "svd", 1)], max_new_tokens=3)
        assert all(v["kl_mean"] == 0.0 for v in r["conditions"]["edited"].values())
    finally:
        ed.close()
