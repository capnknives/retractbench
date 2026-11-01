"""Pick, for each key configuration, the eps at which a fixed share of hard
negatives would trigger (default 5%), from saved separability runs.
Comparing configs at a matched false-trigger rate keeps the comparison fair.

    python scripts/matched_eps.py --cases-tag counterfact_100_seed0 --budget 0.05
"""
import argparse
import glob
import json

ap = argparse.ArgumentParser()
ap.add_argument("--cases-tag", required=True)
ap.add_argument("--budget", type=float, default=0.05)
ap.add_argument("--show-closest", type=int, default=0)
args = ap.parse_args()

for f in sorted(glob.glob(f"results/*_separability_*_{args.cases_tag}.json")):
    d = json.load(open(f, encoding="utf-8"))
    rows = d["rows"]
    hard = sorted(r["distance"] for r in rows if r["kind"] == "hard")
    para = [r["distance"] for r in rows if r["kind"] == "paraphrase"]
    eps = hard[int(args.budget * len(hard))]  # this share of hard negatives sits below eps
    rec = sum(p < eps for p in para) / len(para)
    print(f"{d['meta']['editor']} eps={eps:.4f} predicted_paraphrase_hit={rec:.2f}")
    for r in sorted((r for r in rows if r["kind"] == "hard"), key=lambda r: r["distance"])[: args.show_closest]:
        print(f"    closest hard {r['distance']:.3f} [{r['case_id']}] {r['probe']!r}".encode("ascii", "replace").decode())
