"""Read a run_kl.py result and its truncation control, and compute the numbers the
2026-11-03 18:38 predictions are scored on. Pure Python, reads result files only.

    python scripts/analyze_kl.py <run.json> <control.json> <condition, e.g. svd15> <out.json>

"target" = edited prompt + paraphrases, "away" = unrelated + hard negatives. Ratios
are ratios of means of the per-probe answer KL (mean over positions). The target ratio
gets a case-cluster bootstrap CI (10,000 resamples, seed 0).
"""
import json
import random
import statistics
import sys

TARGET = ("edited_prompt", "paraphrases")
AWAY = ("unrelated", "hard_negatives")


def per_case_sums(run, cond, kinds, key="kl_mean"):
    """{case: (sum, n)} over probes of the given kinds."""
    out = {}
    for cid, r in run["per_case"].items():
        s = n = 0
        for p, v in r["conditions"][cond].items():
            if r["base"][p]["type"] in kinds:
                s += v[key]; n += 1
        out[cid] = (s, n)
    return out


def ratio(a, b, ids):
    num = sum(a[i][0] for i in ids) / max(sum(a[i][1] for i in ids), 1)
    den = sum(b[i][0] for i in ids) / max(sum(b[i][1] for i in ids), 1)
    return num / den if den else float("inf"), num, den


def boot_ratio(a, b, reps=10000, seed=0):
    ids = sorted(a)
    rng = random.Random(seed)
    vals = sorted(ratio(a, b, [ids[rng.randrange(len(ids))] for _ in ids])[0] for _ in range(reps))
    return vals[int(0.025 * reps)], vals[int(0.975 * reps) - 1]


def values(run, cond, kinds, key):
    return [v[key] for r in run["per_case"].values() for p, v in r["conditions"][cond].items()
            if r["base"][p]["type"] in kinds]


def main(run_path, ctrl_path, cond, out_path):
    run = json.load(open(run_path, encoding="utf-8"))
    ctrl = json.load(open(ctrl_path, encoding="utf-8"))
    assert set(run["per_case"]) == set(ctrl["per_case"])
    res = {"run": run_path, "control": ctrl_path, "condition": cond}

    # P1: restore exactly 0; the control's "edited" condition exactly 0
    if "restore" in next(iter(run["per_case"].values()))["conditions"]:
        res["restore_max_kl"] = max(values(run, "restore", TARGET + AWAY, "kl_mean"))
    res["control_edited_max_kl"] = max(values(ctrl, "edited", TARGET + AWAY, "kl_mean"))

    # P2: target and away ratios, undo vs control
    ids = sorted(run["per_case"])
    for name, kinds in (("target", TARGET), ("away", AWAY), ("edited_prompt", ("edited_prompt",)),
                        ("paraphrases", ("paraphrases",)), ("unrelated", ("unrelated",)),
                        ("hard_negatives", ("hard_negatives",))):
        a, b = per_case_sums(run, cond, kinds), per_case_sums(ctrl, cond, kinds)
        r, num, den = ratio(a, b, ids)
        row = {"undo_mean": num, "control_mean": den, "ratio": r,
               "undo_median": statistics.median(values(run, cond, kinds, "kl_mean")),
               "control_median": statistics.median(values(ctrl, cond, kinds, "kl_mean")),
               "edited_mean": ratio(per_case_sums(run, "edited", kinds), b, ids)[1]}
        if name in ("target", "away"):
            row["ratio_ci95"] = boot_ratio(a, b)
        res[f"answer_kl_{name}"] = row

    # P3, P4: first-position KL on the edited prompt
    und = values(run, cond, ("edited_prompt",), "kl_first")
    edi = values(run, "edited", ("edited_prompt",), "kl_first")
    ctl = values(ctrl, cond, ("edited_prompt",), "kl_first")
    res["first_kl_edited_prompt"] = {"undo_mean": statistics.fmean(und), "undo_median": statistics.median(und),
                                     "edited_mean": statistics.fmean(edi), "edited_median": statistics.median(edi),
                                     "control_mean": statistics.fmean(ctl), "control_median": statistics.median(ctl),
                                     "edited_over_undo_mean": statistics.fmean(edi) / statistics.fmean(und)}

    # P5: base top-2 gap where the control's argmax leaves the base token
    gaps, all_gaps = [], []
    for cid, r in ctrl["per_case"].items():
        for p, v in r["conditions"][cond].items():
            g = r["base"][p]["top2_gap"]
            all_gaps += g
            gaps += [g[i] for i in v["argmax_differs_at"]]
    res["control_flip_positions"] = {"n": len(gaps), "median_base_top2_gap": statistics.median(gaps) if gaps else None,
                                     "share_gap_under_1_nat": sum(x < 1 for x in gaps) / len(gaps) if gaps else None,
                                     "median_base_top2_gap_all_positions": statistics.median(all_gaps)}
    json.dump(res, open(out_path, "w", encoding="utf-8", newline="\n"), indent=2)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
