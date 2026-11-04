"""Graded undo test: how far is each model's next-token distribution from the base model's?

For every case and probe (edited prompt, paraphrases, unrelated prompts, hard
negatives), the base model's greedy continuation is generated once; then the edited
model and the model after each undo are run on the same text, and KL(base || model)
is computed at every position (see src/retractbench/divergence.py).

    python scripts/run_kl.py --cases cases/counterfact_100_seed0.jsonl --tag ee_cf100 \
        --deltas data/easyedit_rome/cf100.pt --dtype float32 --modes restore svd --svd-q 3 10 15

With --null-edit every update is replaced by zeros: the truncation control. Its
"edited" condition must then be exactly the base model (KL 0).

Output: results/<timestamp>_kl_<tag>.json with per-probe values and a summary per
condition and probe type (mean and median KL at the first position and over the
whole continuation, and the share of probes whose argmax leaves the base token at
any position).
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from retractbench import provenance
from retractbench.divergence import PROBE_TYPES, case_divergence
from retractbench.editors.precomputed import PrecomputedRomeEditor, load_easyedit_updates
from retractbench.gpu import check_gpu_free
from retractbench.report import load_cases


def summarize(per_case: dict) -> dict:
    out = {}
    first = next(iter(per_case.values()))
    for cond in first["conditions"]:
        rows = {}
        for kind in (*PROBE_TYPES, "all"):
            kf, km, flips = [], [], []
            for r in per_case.values():
                for p, v in r["conditions"][cond].items():
                    if kind != "all" and r["base"][p]["type"] != kind:
                        continue
                    kf.append(v["kl_first"]); km.append(v["kl_mean"]); flips.append(bool(v["argmax_differs_at"]))
            if kf:
                rows[kind] = {"n_probes": len(kf),
                              "kl_first_mean": statistics.fmean(kf), "kl_first_median": statistics.median(kf),
                              "kl_mean_mean": statistics.fmean(km), "kl_mean_median": statistics.median(km),
                              "share_argmax_differs": sum(flips) / len(flips)}
        out[cond] = rows
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    ap.add_argument("--cases", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--deltas", required=True, help="edits exported by scripts/easyedit_rome_export.py")
    ap.add_argument("--dtype", choices=["bfloat16", "float32"], default="float32")
    ap.add_argument("--modes", nargs="+", default=["restore", "svd"], choices=["restore", "subtract", "svd"])
    ap.add_argument("--svd-q", nargs="+", type=int, default=[15], help="one svd condition per value")
    ap.add_argument("--max-new-tokens", type=int, default=8)
    ap.add_argument("--null-edit", action="store_true", help="replace every update by zeros (control)")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    cases = load_cases(args.cases)[: args.limit]
    check_gpu_free()
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=getattr(torch, args.dtype)).to("cuda")
    updates, dmeta, _ = load_easyedit_updates(args.deltas)
    layer = int(dmeta["weight_name"].split(".")[2])
    missing = [c.id for c in cases if c.id not in updates]
    if missing:
        raise SystemExit(f"no stored update for {len(missing)} cases, e.g. {missing[:3]}")
    if args.null_edit:
        updates = {cid: torch.zeros_like(dW) for cid, dW in updates.items()}

    conditions = []
    for mode in args.modes:
        if mode == "svd":
            conditions += [(f"svd{q}", "svd", q) for q in args.svd_q]
        else:
            conditions.append((mode, mode, 0))

    ed = PrecomputedRomeEditor(model, tok, updates, layer=layer, revoke_mode="restore",
                               source="null-edit" if args.null_edit else "easyedit-rome")
    per_case, t0 = {}, time.time()
    try:
        for i, c in enumerate(cases, 1):
            per_case[c.id] = case_divergence(ed, c, conditions, max_new_tokens=args.max_new_tokens)
            s = per_case[c.id]["conditions"]
            msg = " ".join(f"{k}={statistics.fmean(v['kl_mean'] for v in s[k].values()):.4f}" for k in s)
            print(f"  {i}/{len(cases)} {c.id}: mean KL {msg} ({time.time() - t0:.0f}s)", flush=True)
    finally:
        ed.close()

    summary = summarize(per_case)
    meta = {"args": vars(args), "layer": layer, "conditions": conditions,
            "deltas_meta": {k: v for k, v in dmeta.items() if k not in ("context_templates", "hparams")},
            "provenance": provenance.collect({"cases": args.cases, "deltas": args.deltas}, model)}
    out = Path("results") / f"{time.strftime('%Y%m%dT%H%M%S')}_kl_{args.tag}.json"
    out.write_text(json.dumps({"meta": meta, "summary": summary, "per_case": per_case}, indent=1),
                   encoding="utf-8")
    print("\n| condition | probe type | KL first (mean / median) | KL over answer (mean / median) | argmax differs |")
    print("| --- | --- | --- | --- | --- |")
    for cond, rows in summary.items():
        for kind, r in rows.items():
            print(f"| {cond} | {kind} | {r['kl_first_mean']:.4f} / {r['kl_first_median']:.4f} | "
                  f"{r['kl_mean_mean']:.4f} / {r['kl_mean_median']:.4f} | {r['share_argmax_differs']:.2f} |")
    print(f"\nsaved {out}")


if __name__ == "__main__":
    main()
