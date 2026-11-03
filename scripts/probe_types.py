"""Per-probe-type comparison of an SVD undo run with its truncation control.

For each probe type (edited prompt, paraphrases, unrelated, hard negatives) it
counts how many probes equal the base output for: the edited model before any
undo (after_write), the SVD undo (after_revoke) and the control (the control's
after_revoke). On the edited prompt and paraphrases it also counts probes that
differ from base only under the undo, only under the control, how many cases
they fall in, and how many of the undo-only ones contain the edit's target
string. If both runs carry margins, it adds the paired ES comparison (cases
preferring the edit only after the undo vs only under the control, with an
exact two-sided McNemar p-value).

Usage: python scripts/probe_types.py <undo run.json> <control run.json> <cases.jsonl> <out.json>
Pure Python, reads result files only.
"""
import json
import math
import sys


def load_cases(path):
    cases = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                c = json.loads(line)
                cases[c["id"]] = c
    return cases


def probe_types(c):
    return {
        "edited_prompt": [c["prompt"]],
        "paraphrases": list(c["paraphrases"]),
        "unrelated": list(c["unrelated"]),
        "hard_negatives": list(c["hard_negatives"]),
    }


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(p, 1.0)


def main(undo_path, ctrl_path, cases_path, out_path):
    cases = load_cases(cases_path)
    undo = json.load(open(undo_path, encoding="utf-8"))
    ctrl = {r["case_id"]: r for r in json.load(open(ctrl_path, encoding="utf-8"))["cases"]}

    table = {}
    undo_only = ctrl_only = undo_only_with_target = 0
    undo_only_cases = set()
    for r in undo["cases"]:
        c = cases[r["case_id"]]
        r2 = ctrl[r["case_id"]]
        for kind, prompts in probe_types(c).items():
            row = table.setdefault(kind, {"n": 0, "edited_eq_base": 0, "undo_eq_base": 0, "control_eq_base": 0})
            for p in prompts:
                o, o2 = r["outputs"][p], r2["outputs"][p]
                if o["base"] != o2["base"]:
                    raise SystemExit(f"base outputs differ between runs: {r['case_id']} {p!r}")
                row["n"] += 1
                row["edited_eq_base"] += o["after_write"] == o["base"]
                u = o["after_revoke"] == o["base"]
                k = o2["after_revoke"] == o2["base"]
                row["undo_eq_base"] += u
                row["control_eq_base"] += k
                if kind in ("edited_prompt", "paraphrases"):
                    if not u and k:
                        undo_only += 1
                        undo_only_cases.add(r["case_id"])
                        t = c["target"].strip().lower()
                        if t and t in o["after_revoke"].lower() and t not in o["base"].lower():
                            undo_only_with_target += 1
                    if u and not k:
                        ctrl_only += 1

    out = {
        "undo_run": undo_path,
        "control_run": ctrl_path,
        "cases": cases_path,
        "probes_equal_to_base": table,
        "target_probes": {
            "differ_only_after_undo": undo_only,
            "differ_only_under_control": ctrl_only,
            "cases_with_undo_only_difference": len(undo_only_cases),
            "undo_only_containing_target": undo_only_with_target,
        },
    }

    try:
        a = {r["case_id"]: r["margins"]["after_revoke"]["es"] for r in undo["cases"]}
        b = {k: v["margins"]["after_revoke"]["es"] for k, v in ctrl.items()}
        undo_only_es = sum(1 for k in a if a[k] and not b[k])
        ctrl_only_es = sum(1 for k in a if b[k] and not a[k])
        out["es_paired"] = {
            "edit_preferred_only_after_undo": undo_only_es,
            "edit_preferred_only_under_control": ctrl_only_es,
            "mcnemar_exact_p": mcnemar_exact(undo_only_es, ctrl_only_es),
        }
    except (KeyError, TypeError):
        out["es_paired"] = None

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
