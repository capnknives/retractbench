"""Build a retractbench case file from CounterFact (Meng et al., ROME, 2022).

    python scripts/make_counterfact_cases.py --n 100 --seed 0

Downloads counterfact.json into data/ if it isn't there, samples N records
with a fixed seed, and writes cases/counterfact_<N>_seed<seed>.jsonl.

Mapping per record:
- prompt / subject / target: the requested rewrite (target = target_new).
- paraphrases: CounterFact's 2 paraphrase prompts (these start with an
  unrelated sentence, by design).
- hard_negatives: the first `--n-hard` neighborhood prompts. Same relation,
  different subject, whose true answer is the *original* object, so a leaky
  edit shows up as the new target appearing where it shouldn't.
- unrelated: the requested prompts of `--n-easy` other sampled records with a
  different relation_id.

Note: unlike the fictional cases, CounterFact rewrites real facts, so the base
model usually knows the original answer. "Revoked" therefore means "back to
the original answer", not "back to not knowing".
"""
from __future__ import annotations

import argparse
import json
import random
import urllib.request
from pathlib import Path

URL = "https://rome.baulab.info/data/dsets/counterfact.json"
ROOT = Path(__file__).resolve().parent.parent


def load(path: Path) -> list[dict]:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading {URL}")
        urllib.request.urlretrieve(URL, path)
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n-hard", type=int, default=5)
    ap.add_argument("--n-easy", type=int, default=3)
    ap.add_argument("--data", default=str(ROOT / "data" / "counterfact.json"))
    ap.add_argument("--exclude", nargs="*", default=[],
                    help="case files whose records must not be reused (e.g. build a dev set disjoint from the test set)")
    ap.add_argument("--name", default=None, help="output file stem (default counterfact_<n>_seed<seed>)")
    args = ap.parse_args()

    records = load(Path(args.data))
    excluded = set()
    for f in args.exclude:
        for line in open(f, encoding="utf-8"):
            if line.strip() and not line.startswith("#"):
                excluded.add(json.loads(line)["id"])
    records = [r for r in records if f"cf{r['case_id']}" not in excluded]
    rng = random.Random(args.seed)
    picked = rng.sample(records, args.n)

    def prompt_of(r):
        rw = r["requested_rewrite"]
        return rw["prompt"].format(rw["subject"])

    out = ROOT / "cases" / f"{args.name or f'counterfact_{args.n}_seed{args.seed}'}.jsonl"
    with out.open("w", encoding="utf-8", newline="\n") as f:
        cmd = f"python scripts/make_counterfact_cases.py --n {args.n} --seed {args.seed}"
        if args.exclude:
            cmd += " --exclude " + " ".join(args.exclude)
        if args.name:
            cmd += f" --name {args.name}"
        f.write(f"# Sampled from CounterFact ({URL}) with `{cmd}`.\n")
        for r in picked:
            rw = r["requested_rewrite"]
            others = [o for o in picked if o["requested_rewrite"]["relation_id"] != rw["relation_id"]]
            easy = [prompt_of(o) for o in rng.sample(others, args.n_easy)]
            case = {
                "id": f"cf{r['case_id']}",
                "subject": rw["subject"],
                "prompt": prompt_of(r),
                "target": " " + rw["target_new"]["str"],
                "target_true": " " + rw["target_true"]["str"],
                "relation_id": rw["relation_id"],
                "paraphrases": r["paraphrase_prompts"],
                "unrelated": easy,
                "hard_negatives": r["neighborhood_prompts"][: args.n_hard],
            }
            f.write(json.dumps(case, ensure_ascii=False) + "\n")
    print(f"wrote {out} ({args.n} cases)")


if __name__ == "__main__":
    main()
