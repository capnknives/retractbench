"""Compare the SVD undo of real edits with the same truncation on the unedited model.

    python scripts/compare_null_svd.py <edited svd run>.json <null-edit svd run>.json <out>.json

Both runs must cover the same cases with the same probes and settings (made by
run_rome.py with --modes svd and the same --svd-q, the second with --null-edit).
For every case and probe there are three outputs to compare:
  base            the unedited model
  null_svd        the unedited model with its top-q components dropped
  edited_svd      the edited model with its top-q components dropped (the undo)
Reported, over cases and over probes:
  null_exact      null_svd == base on every probe (how much truncation alone changes)
  edited_exact    edited_svd == base on every probe (the headline exact-revoke rate)
  edited_eq_null  edited_svd == null_svd on every probe (the edit is gone, up to truncation damage)
plus the per-probe rates of each, and the null run's own leak rate (how often
the target string shows up after truncation without any edit).
"""
import json
import sys
from pathlib import Path


def _load(path):
    run = json.loads(Path(path).read_text(encoding="utf-8"))
    return run, {r["case_id"]: r for r in run["cases"]}


def main(edited_path, null_path, out_path):
    e_run, edited = _load(edited_path)
    n_run, null = _load(null_path)
    if set(edited) != set(null):
        raise SystemExit("the two runs cover different cases")
    case_rows = []
    probes_total = 0
    probe_counts = {"null_eq_base": 0, "edited_eq_base": 0, "edited_eq_null": 0}
    for cid in sorted(edited):
        eo, no = edited[cid]["outputs"], null[cid]["outputs"]
        if set(eo) != set(no):
            raise SystemExit(f"case {cid}: the two runs used different probes")
        for p in eo:
            if eo[p]["base"] != no[p]["base"]:
                raise SystemExit(f"case {cid}: base outputs differ between runs, so they are not comparable")
        rows = {p: (eo[p]["base"], no[p]["after_revoke"], eo[p]["after_revoke"]) for p in eo}
        n = len(rows)
        probes_total += n
        c = {
            "null_eq_base": sum(nb == b for b, nb, _ in rows.values()),
            "edited_eq_base": sum(es == b for b, _, es in rows.values()),
            "edited_eq_null": sum(es == nb for _, nb, es in rows.values()),
        }
        for k in probe_counts:
            probe_counts[k] += c[k]
        case_rows.append({"case": cid, "n_probes": n, **c})
    n_cases = len(case_rows)
    summary = {
        "n_cases": n_cases,
        "n_probes": probes_total,
        "null_exact": sum(r["null_eq_base"] == r["n_probes"] for r in case_rows),
        "edited_exact": sum(r["edited_eq_base"] == r["n_probes"] for r in case_rows),
        "edited_eq_null_all_probes": sum(r["edited_eq_null"] == r["n_probes"] for r in case_rows),
        "probe_null_eq_base": probe_counts["null_eq_base"],
        "probe_edited_eq_base": probe_counts["edited_eq_base"],
        "probe_edited_eq_null": probe_counts["edited_eq_null"],
        "null_target_leak_mean": n_run["summary"].get("target_leak_after_revoke"),
        "edited_target_leak_mean": e_run["summary"].get("target_leak_after_revoke"),
        "edited_run": str(edited_path),
        "null_run": str(null_path),
    }
    Path(out_path).write_text(json.dumps({"summary": summary, "cases": case_rows}, indent=1), encoding="utf-8")
    for k, v in summary.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
