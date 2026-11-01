"""Pure-Python checks for the separability statistics."""
import math

import pytest

from retractbench.separability import auc, rate_below, recall_at_budget, summarize_distances


def test_auc_perfect_random_and_inverted():
    assert auc([0.1, 0.2], [0.5, 0.6]) == 1.0
    assert auc([0.5, 0.6], [0.1, 0.2]) == 0.0
    assert auc([0.3], [0.3]) == 0.5
    assert math.isnan(auc([], [0.1]))


def test_rate_below_is_strict():
    assert rate_below([0.1, 0.2, 0.3], 0.2) == pytest.approx(1 / 3)


def test_recall_at_budget_finds_best_threshold():
    para = [0.05, 0.10, 0.30]
    hard = [0.20, 0.40, 0.50, 0.60]
    r, e = recall_at_budget(para, hard, budget=0.0)
    assert r == pytest.approx(2 / 3)       # 0.05 and 0.10 caught, no hard negative below
    assert 0.10 < e <= 0.20
    r, _ = recall_at_budget(para, hard, budget=0.25)
    assert r == 1.0                        # allowing 1 of 4 hard hits catches 0.30 too


def test_summary_shape():
    rows = [{"kind": "paraphrase", "distance": 0.1}, {"kind": "hard", "distance": 0.2},
            {"kind": "easy", "distance": 0.5}]
    s = summarize_distances(rows, [0.15, 0.3])
    assert s["auc_paraphrase_vs_hard"] == 1.0
    assert s["grid"][0] == {"eps": 0.15, "paraphrase_hit": 1.0, "hard_hit": 0.0, "easy_hit": 0.0}
    assert s["paraphrase_recall_at_5pct_hard"] == 1.0
