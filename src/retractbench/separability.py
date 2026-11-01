"""Can any single threshold separate paraphrases from look-alike negatives?

For a distance-keyed editor (GRACE and variants), the edit fires on a probe
when the probe's distance to the edit's key is below eps. So before training
anything, we can measure each probe's distance and ask:

- AUC(paraphrase vs hard negative): probability that a random paraphrase is
  closer to its key than a random hard negative is to its key. 1.0 means some
  eps separates them perfectly; 0.5 means distance carries no signal.
- For each eps: the share of paraphrases, hard negatives and easy negatives
  that would trigger.
- Paraphrase recall at a fixed false-trigger budget: the best paraphrase
  hit rate achievable while at most 5% (or 1%) of hard negatives trigger.

Caveat: this checks prompt tokens only. At inference the editor also checks
generated tokens, which can add triggers (see LOG.md, Chicago Bulls probe).
The pure-Python parts are torch-free and tested in tests/test_separability.py.
"""
from __future__ import annotations

from typing import Iterable

from .types import EditCase

KINDS = ("paraphrase", "hard", "easy")


def auc(pos: list[float], neg: list[float]) -> float:
    """P(pos distance < neg distance), ties count half. Smaller distance = 'positive'."""
    if not pos or not neg:
        return float("nan")
    wins = sum((p < n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def rate_below(xs: list[float], eps: float) -> float:
    return sum(x < eps for x in xs) / len(xs) if xs else float("nan")


def recall_at_budget(para: list[float], hard: list[float], budget: float) -> tuple[float, float]:
    """Best paraphrase hit rate with hard-negative hit rate <= budget.
    Returns (recall, eps that achieves it)."""
    best = (0.0, 0.0)
    for eps in sorted(set(para + hard)):
        for e in (eps, eps + 1e-9):  # just below and just above each observed distance
            if rate_below(hard, e) <= budget:
                r = rate_below(para, e)
                if r > best[0]:
                    best = (r, e)
    return best


def summarize_distances(rows: list[dict], eps_grid: Iterable[float]) -> dict:
    by = {k: [r["distance"] for r in rows if r["kind"] == k] for k in KINDS}
    out = {
        "n_probes": {k: len(v) for k, v in by.items()},
        "auc_paraphrase_vs_hard": auc(by["paraphrase"], by["hard"]),
        "auc_paraphrase_vs_easy": auc(by["paraphrase"], by["easy"]),
        "median": {k: (sorted(v)[len(v) // 2] if v else float("nan")) for k, v in by.items()},
        "grid": [
            {"eps": e, **{f"{k}_hit": rate_below(by[k], e) for k in KINDS}} for e in eps_grid
        ],
    }
    for budget in (0.01, 0.05):
        r, e = recall_at_budget(by["paraphrase"], by["hard"], budget)
        out[f"paraphrase_recall_at_{int(budget * 100)}pct_hard"] = r
        out[f"eps_at_{int(budget * 100)}pct_hard"] = e
    return out


def measure(editor, cases: list[EditCase], progress: bool = False) -> list[dict]:
    """Distance from each case's key to each of its probes. Needs an editor with
    `case_key(case)` and `probe_distance(key, prompt)` (GraceEditor has both)."""
    rows = []
    for i, c in enumerate(cases, 1):
        key = editor.case_key(c)
        for kind, probes in zip(KINDS, (c.paraphrases, c.hard_negatives, c.unrelated)):
            for p in probes:
                rows.append({"case_id": c.id, "kind": kind, "probe": p,
                             "distance": editor.probe_distance(key, p)})
        if progress and i % 20 == 0:
            print(f"  separability {i}/{len(cases)}", flush=True)
    return rows
