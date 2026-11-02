"""Choose q for the SVD-truncation undo (Youssef et al., ICLR 2026) on held-out cases.

The paper picks its truncation level per model by reversal accuracy on the
edited prompt. We do the same, but on a dev set that shares no records with
the test set, so the test numbers aren't tuned on themselves.

For each dev case: record the base prediction, apply the ROME-style edit, then
for each q in the range drop the top-q singular components of the *edited*
matrix and regenerate the edited prompt.
  reversal = prediction equals the base model's prediction (paper's criterion)
  edit_kept = prediction still starts with the new target
Picks the q with the highest reversal rate (ties: smallest q).

    python scripts/sweep_svd_q.py --cases cases/counterfact_dev20_seed1.jsonl --qmax 20
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from retractbench.editors.rome import RomeEditor, drop_top_singular
from retractbench.gpu import check_gpu_free
from retractbench.harness import answers_with_target
from retractbench.report import load_cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    ap.add_argument("--cases", required=True)
    ap.add_argument("--layer", type=int, default=4)
    ap.add_argument("--covariance", default="calibration", choices=["identity", "calibration"])
    ap.add_argument("--qmax", type=int, default=20)
    ap.add_argument("--tokens", type=int, default=5, help="tokens generated per check (paper uses 5)")
    args = ap.parse_args()

    cases = load_cases(args.cases)
    check_gpu_free()
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16).to("cuda")
    ed = RomeEditor(model, tok, layer=args.layer, revoke_mode="restore", covariance=args.covariance)
    qs = list(range(0, args.qmax + 1))
    rev = {q: 0 for q in qs}
    kept = {q: 0 for q in qs}
    n_ok = 0
    t0 = time.time()
    try:
        for i, c in enumerate(cases, 1):
            base = ed.generate(c.prompt, args.tokens)
            h = ed.apply(c)
            edited_W = ed.W.detach().clone()
            if not answers_with_target(ed.generate(c.prompt, args.tokens), c.target):
                ed.reset()
                print(f"  case {i}/{len(cases)} {c.id}: edit failed, skipped", flush=True)
                continue
            n_ok += 1
            for q in qs:
                with torch.no_grad():
                    ed.W.copy_(drop_top_singular(edited_W, q).to(ed.W.dtype))
                out = ed.generate(c.prompt, args.tokens)
                rev[q] += out == base
                kept[q] += answers_with_target(out, c.target)
            ed.reset()
            print(f"  case {i}/{len(cases)} {c.id} ({time.time() - t0:.0f}s)", flush=True)
    finally:
        ed.close()

    table = [{"q": q, "reversal": rev[q] / max(n_ok, 1), "edit_kept": kept[q] / max(n_ok, 1)} for q in qs]
    best = max(table, key=lambda r: (r["reversal"], -r["q"]))
    out = Path("results") / f"{time.strftime('%Y%m%dT%H%M%S')}_svd_q_sweep.json"
    out.write_text(json.dumps({"cases_file": args.cases, "model": args.model, "layer": args.layer,
                               "covariance": args.covariance, "n_edits_ok": n_ok, "table": table,
                               "best_q": best["q"]}, indent=2), encoding="utf-8")
    print("\n| q | reversal (= base prediction) | edit kept |")
    print("| --- | --- | --- |")
    for r in table:
        print(f"| {r['q']} | {r['reversal']:.2f} | {r['edit_kept']:.2f} |")
    print(f"\nBEST_Q={best['q']} (reversal {best['reversal']:.2f}) on {n_ok} successful edits\nsaved {out}\nALL DONE")


if __name__ == "__main__":
    main()
