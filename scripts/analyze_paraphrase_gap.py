"""Why do fewer paraphrases succeed than separability predicts?

Joins a separability run (prompt-token distances) with the matching benchmark
run (actual generations) and sorts every paraphrase into:
  fired+answered   distance < eps and the target appeared
  fired+wrong      distance < eps but the target did not appear
  missed           distance >= eps and the target did not appear
  answered-anyway  distance >= eps but the target appeared (e.g. triggered on a
                   generated token, or the base model already leaned that way)

    python scripts/analyze_paraphrase_gap.py --editor grace-subject-raw --tag cf100
"""
import argparse
import glob
import json
import sys
from collections import Counter

sys.path.insert(0, "src")
from retractbench.harness import answers_with_target, mentions_target  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--editor", default="grace-subject-raw")
ap.add_argument("--tag", default="cf100")
ap.add_argument("--cases", default="cases/counterfact_100_seed0.jsonl")
ap.add_argument("--examples", type=int, default=4)
args = ap.parse_args()

sep_file = sorted(glob.glob(f"results/*_separability_{args.editor}_{args.tag}.json"))[-1]
run_file = sorted(glob.glob(f"results/*_{args.editor}_{args.tag}.json"))
run_file = [f for f in run_file if "_separability_" not in f][-1]
sep = json.load(open(sep_file, encoding="utf-8"))
run = json.load(open(run_file, encoding="utf-8"))
eps = run["meta"]["editor_config"]["eps"]
targets = {}
for line in open(args.cases, encoding="utf-8"):
    if line.strip() and not line.startswith("#"):
        d = json.loads(line)
        targets[d["id"]] = d["target"]
outputs = {c["case_id"]: c["outputs"] for c in run["cases"]}

buckets, examples = Counter(), {}
for r in sep["rows"]:
    if r["kind"] != "paraphrase":
        continue
    o = outputs[r["case_id"]][r["probe"]]
    t = targets[r["case_id"]]
    answered = mentions_target(o["after_write"], t) and not mentions_target(o["base"], t)
    fired = r["distance"] < eps
    b = {(True, True): "fired+answered", (True, False): "fired+wrong",
         (False, False): "missed", (False, True): "answered-anyway"}[(fired, answered)]
    buckets[b] += 1
    examples.setdefault(b, []).append((r["case_id"], r["distance"], r["probe"], t, o["after_write"], o["base"]))

n = sum(buckets.values())
print(f"{args.editor} on {args.tag}: eps={eps:.4f}, {n} paraphrases")
for b in ("fired+answered", "fired+wrong", "missed", "answered-anyway"):
    print(f"  {b:16s} {buckets[b]:4d}  ({buckets[b] / n:.0%})")

def show(s):
    return s.encode("ascii", "replace").decode()

for b in ("fired+wrong", "missed"):
    print(f"\nExamples: {b}")
    for cid, d, probe, t, after, base in examples.get(b, [])[: args.examples]:
        print(f"  [{cid}] d={d:.3f} target={show(t)!r}")
        print(f"     probe: {show(probe)!r}")
        print(f"     edited: {show(after)!r}   base: {show(base)!r}")

print("\nStrict edit misses (exact prompt):")
for c in run["cases"]:
    if not c["edit_success"]:
        o = c["outputs"]
        prompt = next(iter(o))
        print(f"  [{c['case_id']}] target={show(targets[c['case_id']])!r} edited={show(o[prompt]['after_write'])!r}")
