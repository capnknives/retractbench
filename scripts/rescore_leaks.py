"""Recompute leak counts for saved runs from their stored outputs (no model needed).

Added with the target_leak_excl_true metric (2026-11-02). Reads each run's
per-probe base and after-revoke outputs, recomputes the plain and the
true-object-excluding leak counts with harness.leak_flags, and writes a new
results file. The original run files are not modified.

    python scripts/rescore_leaks.py results/*_cf100_L4_iso.json
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from retractbench.harness import leak_flags
from retractbench.report import load_cases


def rescore(path: Path) -> dict:
    run = json.loads(path.read_text(encoding="utf-8"))
    cases_file = run["meta"].get("extra", run["meta"]).get("cases_file") or run["meta"].get("cases_file")
    cases = {c.id: c for c in load_cases(cases_file)}
    per_case, plain_all, strict_all = [], [], []
    for r in run["cases"]:
        c = cases[r["case_id"]]
        base = {p: o["base"] for p, o in r["outputs"].items()}
        after = {p: o["after_revoke"] for p, o in r["outputs"].items()}
        plain = leak_flags(c, base, after)
        strict = leak_flags(c, base, after, exclude_true=True)
        plain_all.append(sum(plain) / len(plain))
        strict_all.append(sum(strict) / len(strict))
        if any(plain):
            per_case.append({"case_id": c.id, "target": c.target, "target_true": c.target_true,
                             "plain": plain, "excl_true": strict,
                             "after_revoke": {p: after[p] for p in [c.prompt, *c.paraphrases]}})
    stored = run["summary"].get("target_leak_after_revoke")
    return {"file": str(path), "editor": run["meta"].get("editor"), "n_cases": len(run["cases"]),
            "stored_target_leak_after_revoke": stored,
            "target_leak_after_revoke": sum(plain_all) / len(plain_all),
            "target_leak_excl_true": sum(strict_all) / len(strict_all),
            "cases_with_plain_leak": sum(any(x["plain"]) for x in per_case),
            "cases_with_strict_leak": sum(any(x["excl_true"]) for x in per_case),
            "leaky_cases": per_case}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    args = ap.parse_args()
    rows = [rescore(Path(p)) for p in args.runs if not p.endswith("_editorlog.json")]
    out = Path("results") / f"{time.strftime('%Y%m%dT%H%M%S')}_rescore_leaks.json"
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print("| run | leak (stored) | leak (recomputed) | leak excl. true | cases: plain / strict |")
    print("| --- | --- | --- | --- | --- |")
    for r in rows:
        print(f"| {r['editor']} | {r['stored_target_leak_after_revoke']:.3f} | {r['target_leak_after_revoke']:.3f} | "
              f"{r['target_leak_excl_true']:.3f} | {r['cases_with_plain_leak']} / {r['cases_with_strict_leak']} |")
        for x in r["leaky_cases"]:
            flag = "" if any(x["excl_true"]) else "   (not counted by excl_true)"
            print(f"    {x['case_id']} target={x['target']!r} true={x['target_true']!r}: "
                  f"{list(x['after_revoke'].values())[0]!r}{flag}")
    print(f"\nsaved {out}")


if __name__ == "__main__":
    main()
