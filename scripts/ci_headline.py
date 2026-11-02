"""95% confidence intervals for the write-up's headline rates, read from the result files.

    python scripts/ci_headline.py --runs results/<restore>.json results/<subtract>.json results/<svd3>.json
        --stat results/<stat_undo>.json --sweep results/<svd_q_sweep>.json --out results/<ts>_ci_headline.json

- Rates counted once per case (exact revoke, test rejected, reversal in the sweep): Wilson score
  interval. Unlike the textbook p +/- 1.96 * sqrt(p(1-p)/n), it stays sensible at 0/100 or 1/100.
- Target leak is counted per probe, but the 3 target probes of one case are not independent
  (an edit that survives tends to survive on all three). So its interval comes from a bootstrap
  over cases: resample the 100 cases with replacement, recompute the probe-level rate, and take
  the 2.5% and 97.5% percentiles.
"""
import argparse
import json
import math
import random
from pathlib import Path


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def bootstrap_mean_of_ratio(pairs: list[tuple[int, int]], reps: int = 10000, seed: int = 0):
    """pairs = (flags, probes) per case; statistic = sum(flags) / sum(probes)."""
    rng = random.Random(seed)
    stats = []
    for _ in range(reps):
        s = [rng.choice(pairs) for _ in pairs]
        stats.append(sum(a for a, _ in s) / sum(b for _, b in s))
    stats.sort()
    return stats[int(0.025 * reps)], stats[int(0.975 * reps) - 1]


def row(label, k, n, lo, hi):
    return {"label": label, "k": k, "n": n, "rate": k / n if n else float("nan"), "ci95": [lo, hi]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", default=[])
    ap.add_argument("--stat")
    ap.add_argument("--sweep")
    ap.add_argument("--out")
    args = ap.parse_args()
    rows = []

    for path in args.runs:
        run = json.loads(Path(path).read_text(encoding="utf-8"))
        name = run["meta"]["editor"]
        cases = run["cases"]
        n = len(cases)
        k = sum(bool(c["revocation_exact"]) for c in cases)
        rows.append(row(f"{name}: exact revoke", k, n, *wilson(k, n)))
        # target probes per case = edited prompt + paraphrases; leak rate per case is flags / probes
        pairs = []
        for c in cases:
            n_probes = 1 + sum(1 for p in c["outputs"]) * 0  # placeholder replaced below
            pairs.append(c)
        pairs = [(round(c["target_leak_after_revoke"] * c["_n_target"]), c["_n_target"])
                 for c in cases] if cases and "_n_target" in cases[0] else None
        if pairs is None:
            # every CounterFact case here has the edited prompt + 2 paraphrases = 3 target probes
            pairs = [(round(c["target_leak_after_revoke"] * 3), 3) for c in cases]
        k_leak, n_leak = sum(a for a, _ in pairs), sum(b for _, b in pairs)
        if k_leak == 0:
            # A bootstrap of all-zero data gives [0, 0], which claims too much. Use Wilson over
            # cases instead: "no case leaked" in 100 cases bounds the leaking share of cases.
            n_cases_ = len(pairs)
            rows.append(row(f"{name}: target leak (0 flags; Wilson over {n_cases_} cases)",
                            0, n_leak, *wilson(0, n_cases_)))
        else:
            rows.append(row(f"{name}: target leak (per probe, case bootstrap)", k_leak, n_leak,
                            *bootstrap_mean_of_ratio(pairs)))

    if args.stat:
        st = json.loads(Path(args.stat).read_text(encoding="utf-8"))
        for s in st["summary"]:
            n = s["n_cases"]
            k = round(s["reject_rate"] * n)
            rows.append(row(f"MMD test rejects at 0.05: {s['comparison']}", k, n, *wilson(k, n)))

    if args.sweep:
        sw = json.loads(Path(args.sweep).read_text(encoding="utf-8"))
        for t in sw["table"]:
            n = t["n"]
            for key, what in (("reversal_1", "first token"), ("reversal", "all 5 tokens")):
                k = round(t[key] * n)
                rows.append(row(f"dev sweep q={t['q']}: reversal, {what}", k, n, *wilson(k, n)))

    for r in rows:
        lo, hi = r["ci95"]
        print(f"{r['label']:<60} {r['k']:>4}/{r['n']:<4} {r['rate']:6.3f}  [{lo:.3f}, {hi:.3f}]")
    if args.out:
        Path(args.out).write_text(json.dumps(rows, indent=1), encoding="utf-8")
        print("saved", args.out)


if __name__ == "__main__":
    main()
