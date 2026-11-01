"""Compare key configurations at a matched false-trigger rate.

For each (key_position, key_space):
  1. measure separability on the case set,
  2. pick eps so that `--budget` of hard negatives fall below it,
  3. run the full revocation benchmark at that eps.
The model is loaded once. Everything is saved under results/.

    python scripts/run_matched.py --cases cases/counterfact_100_seed0.jsonl --tag cf100
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from retractbench.editors.grace import GraceEditor
from retractbench.harness import run_suite, summarize
from retractbench.report import load_cases, run_meta, save_run
from retractbench.separability import measure, summarize_distances

GRID = [0.005, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    ap.add_argument("--cases", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--budget", type=float, default=0.05)
    ap.add_argument("--configs", nargs="+",
                    default=["last:raw", "last:standardized", "subject:raw", "subject:standardized"])
    ap.add_argument("--max-new-tokens", type=int, default=8)
    args = ap.parse_args()

    cases = load_cases(args.cases)
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16).to("cuda")
    extra = {"model": args.model, "device": "cuda", "dtype": "bfloat16", "cases_file": args.cases,
             "n_cases": len(cases), "torch": torch.__version__, "budget": args.budget}
    out = Path("results")
    table = []

    for cfg in args.configs:
        kp, ks = cfg.split(":")
        t0 = time.time()
        ed = GraceEditor(model, tok, key_position=kp, key_space=ks)
        try:
            rows = measure(ed, cases, progress=True)
            sep = summarize_distances(rows, GRID)
            meta = run_meta(ed.name, ed.config(), extra)
        finally:
            ed.close()
        (out / f"{meta['timestamp_utc']}_separability_{ed.name}_{args.tag}.json").write_text(
            json.dumps({"meta": meta, "summary": sep, "rows": rows}, indent=2), encoding="utf-8")
        hard = sorted(r["distance"] for r in rows if r["kind"] == "hard")
        eps = hard[int(args.budget * len(hard))]
        print(f"[{cfg}] AUC para/hard {sep['auc_paraphrase_vs_hard']:.3f}, eps@{args.budget:.0%} hard = {eps:.4f}",
              flush=True)

        ed = GraceEditor(model, tok, key_position=kp, key_space=ks, eps=eps)
        try:
            results = run_suite(ed, cases, max_new_tokens=args.max_new_tokens, progress=True)
            s = summarize(results)
            jp, _ = save_run(results, s, ed.name, ed.config(), extra=extra, tag=args.tag)
        finally:
            ed.close()
        row = {"config": cfg, "eps": eps, "auc_para_vs_hard": sep["auc_paraphrase_vs_hard"],
               "fallbacks": len(ed.fallback_cases), "minutes": (time.time() - t0) / 60, **s}
        table.append(row)
        print(json.dumps(row), flush=True)

    summary_path = out / f"{time.strftime('%Y%m%dT%H%M%S')}_matched_{args.tag}.json"
    summary_path.write_text(json.dumps(table, indent=2), encoding="utf-8")
    print("\n| config | eps | AUC p/hard | edit | edit (loose) | para gen | locality | locality hard | exact revoke | leak |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in table:
        print(f"| {r['config']} | {r['eps']:.4f} | {r['auc_para_vs_hard']:.3f} | {r['edit_success']:.2f} | "
              f"{r['edit_success_loose']:.2f} | {r['paraphrase_generalization']:.2f} | {r['locality']:.2f} | "
              f"{r['locality_hard']:.2f} | {r['revocation_exact']:.2f} | {r['target_leak_after_revoke']:.2f} |")
    print(f"\nsaved {summary_path}\nALL DONE")


if __name__ == "__main__":
    main()
