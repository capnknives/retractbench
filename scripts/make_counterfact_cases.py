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

Second selection mode, which reproduces how Youssef et al. choose facts
(trace-and-reverse, src/reversing_single_edits.py, `run`):

    python scripts/make_counterfact_cases.py --per-relation 2 --name counterfact_rel31x2

Groups the whole file by requested_rewrite.relation_id, keeps the relations
with at least `--min-relation-size` records (default 200, 31 relations in
CounterFact), and takes the first K records of each in dataset order. Output
order is by first appearance of each relation. The authors' script indexes the
records of a relation with `--instance_id` (0, 1, ...), so K=2 is their
instance_id 0 and 1 for every relation; nothing else is filtered at selection.
Differences, stated plainly:
- Their script drops an edit afterwards if EasyEdit's own post-edit
  rewrite_acc is below 1.0 ("unsuccessful edit"). That needs a model, so it is
  not applied here; scripts/easyedit_rome_export.py records rewrite_acc_post
  per case, and sweep_svd_q.py reports a table restricted to those that pass.
- Relation sizes are counted on the whole file, before `--exclude`; excluded
  records are then skipped and the next ones in order are taken. With no
  --exclude this is exactly their pick.
- `unrelated` prompts are drawn with the seeded rng from the picked records of
  other relations, as in the random mode (the paper has no such probes).
Without --per-relation the random mode below is unchanged.

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


def default_name(args) -> str:
    if args.per_relation is not None:
        return f"counterfact_rel{args.per_relation}_seed{args.seed}"
    return f"counterfact_{args.n}_seed{args.seed}"


def pick_per_relation(records: list[dict], k: int, min_size: int, excluded: set[str]) -> list[dict]:
    """First k records, in dataset order, of every relation with at least min_size records."""
    by_rel: dict[str, list[dict]] = {}
    for r in records:
        by_rel.setdefault(r["requested_rewrite"]["relation_id"], []).append(r)
    picked = []
    for rel_records in by_rel.values():
        if len(rel_records) >= min_size:
            picked += [r for r in rel_records if f"cf{r['case_id']}" not in excluded][:k]
    return picked


def render(picked: list[dict], rng: random.Random, cmd: str, n_hard: int, n_easy: int) -> str:
    """The case file text. The rng is used only for the `unrelated` prompts (and, in random mode, was used to pick)."""
    def prompt_of(r):
        rw = r["requested_rewrite"]
        return rw["prompt"].format(rw["subject"])

    lines = [f"# Sampled from CounterFact ({URL}) with `{cmd}`.\n"]
    for r in picked:
        rw = r["requested_rewrite"]
        others = [o for o in picked if o["requested_rewrite"]["relation_id"] != rw["relation_id"]]
        easy = [prompt_of(o) for o in rng.sample(others, n_easy)]
        case = {
            "id": f"cf{r['case_id']}",
            "subject": rw["subject"],
            "prompt": prompt_of(r),
            "target": " " + rw["target_new"]["str"],
            "target_true": " " + rw["target_true"]["str"],
            "relation_id": rw["relation_id"],
            "paraphrases": r["paraphrase_prompts"],
            "unrelated": easy,
            "hard_negatives": r["neighborhood_prompts"][: n_hard],
        }
        lines.append(json.dumps(case, ensure_ascii=False) + "\n")
    return "".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n-hard", type=int, default=5)
    ap.add_argument("--n-easy", type=int, default=3)
    ap.add_argument("--data", default=str(ROOT / "data" / "counterfact.json"))
    ap.add_argument("--exclude", nargs="*", default=[],
                    help="case files whose records must not be reused (e.g. build a dev set disjoint from the test set)")
    ap.add_argument("--per-relation", type=int, default=None, metavar="K",
                    help="paper-style pick: the first K records in dataset order of each large relation (ignores --n)")
    ap.add_argument("--min-relation-size", type=int, default=None, metavar="N",
                    help="with --per-relation: smallest relation to use (default 200)")
    ap.add_argument("--name", default=None, help="output file stem (default counterfact_<n>_seed<seed>)")
    args = ap.parse_args()

    records = load(Path(args.data))
    excluded = set()
    for f in args.exclude:
        for line in open(f, encoding="utf-8"):
            if line.strip() and not line.startswith("#"):
                excluded.add(json.loads(line)["id"])
    rng = random.Random(args.seed)
    if args.per_relation is None:
        if args.min_relation_size is not None:
            ap.error("--min-relation-size needs --per-relation")
        records = [r for r in records if f"cf{r['case_id']}" not in excluded]
        picked = rng.sample(records, args.n)
        cmd = f"python scripts/make_counterfact_cases.py --n {args.n} --seed {args.seed}"
    else:
        size = 200 if args.min_relation_size is None else args.min_relation_size
        picked = pick_per_relation(records, args.per_relation, size, excluded)
        cmd = (f"python scripts/make_counterfact_cases.py --per-relation {args.per_relation} "
               f"--min-relation-size {size} --seed {args.seed} --n-hard {args.n_hard} --n-easy {args.n_easy}")
    if args.exclude:
        cmd += " --exclude " + " ".join(args.exclude)
    if args.name:
        cmd += f" --name {args.name}"

    out = ROOT / "cases" / f"{args.name or default_name(args)}.jsonl"
    out.write_text(render(picked, rng, cmd, args.n_hard, args.n_easy), encoding="utf-8", newline="\n")
    print(f"wrote {out} ({len(picked)} cases)")


if __name__ == "__main__":
    main()
