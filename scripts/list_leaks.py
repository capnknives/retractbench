"""List every leak flag of a run, for hand-labelling, with an automatic first sort.

    python scripts/list_leaks.py results/<run>.json cases/<cases>.jsonl <out>.json

Uses harness.leak_flags, so the flags are exactly the ones the summary counted.
Each flagged probe is put in one of three groups before reading:
  survived  after-revoke output == edited-model output (the undo did nothing on this probe)
  mixed     after-revoke output names the target and the true object
  other     everything else
Writes a JSON list; the labels themselves are added by hand.
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from retractbench.harness import leak_flags  # noqa: E402
from retractbench.report import load_cases  # noqa: E402


def main(run_path, cases_path, out_path):
    run = json.loads(Path(run_path).read_text(encoding="utf-8"))
    cases = {c.id: c for c in load_cases(cases_path)}
    rows = []
    for r in run["cases"]:
        case = cases[r["case_id"]]
        outs = r["outputs"]
        base = {p: o["base"] for p, o in outs.items()}
        after = {p: o["after_revoke"] for p, o in outs.items()}
        probes = [case.prompt, *case.paraphrases]   # the order leak_flags uses
        for p, flag in zip(probes, leak_flags(case, base, after)):
            if not flag:
                continue
            w = outs[p]["after_write"]
            true = (case.target_true or "").strip().lower()
            group = "survived" if after[p] == w else ("mixed" if true and true in after[p].lower() else "other")
            rows.append({"case": case.id, "target": case.target, "true": case.target_true, "prompt": p,
                         "base": base[p], "after_write": w, "after_revoke": after[p], "group": group})
    Path(out_path).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(rows)} leak flags in {len({x['case'] for x in rows})} cases: {dict(Counter(x['group'] for x in rows))}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
