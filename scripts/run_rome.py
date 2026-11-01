"""Run the ROME-style editor over layers x undo modes, loading the model once.

    python scripts/run_rome.py --cases cases/counterfact_100_seed0.jsonl --tag cf100 \
        --layers 7 --modes restore subtract inverse

Saves each run with save_run, plus per-case fit and revoke logs.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from retractbench.editors.rome import RomeEditor
from retractbench.gpu import check_gpu_free
from retractbench.harness import run_suite, summarize
from retractbench.report import load_cases, save_run


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    ap.add_argument("--cases", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--layers", type=int, nargs="+", default=[7])
    ap.add_argument("--modes", nargs="+", default=["restore", "subtract", "inverse"])
    ap.add_argument("--covariance", default="identity", choices=["identity", "calibration"])
    ap.add_argument("--weight-dtype", default="float32", choices=["float32", "native"])
    ap.add_argument("--key-position", default="subject", choices=["subject", "last"])
    ap.add_argument("--inverse-target", default="base", choices=["base", "true"])
    ap.add_argument("--max-new-tokens", type=int, default=8)
    ap.add_argument("--no-isolate", action="store_true",
                    help="keep residue between cases (measures accumulated drift)")
    args = ap.parse_args()

    cases = load_cases(args.cases)[: args.limit]
    check_gpu_free()
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16).to("cuda")
    extra = {"model": args.model, "device": "cuda", "dtype": "bfloat16", "cases_file": args.cases,
             "n_cases": len(cases), "torch": torch.__version__}
    table = []

    for layer in args.layers:
        base_cache = None if args.no_isolate else {}  # the fp32 wrapper is part of the "base" model
        for mode in args.modes:
            t0 = time.time()
            ed = RomeEditor(model, tok, layer=layer, key_position=args.key_position, revoke_mode=mode,
                            covariance=args.covariance, weight_dtype=args.weight_dtype,
                            inverse_target=args.inverse_target)
            print(f"[{ed.name} layer {layer}]", flush=True)
            try:
                results = run_suite(ed, cases, max_new_tokens=args.max_new_tokens, progress=True,
                                    base_cache=base_cache, isolate=not args.no_isolate)
                s = summarize(results)
                tag = f"{args.tag}_L{layer}_{'cum' if args.no_isolate else 'iso'}"
                jp, _ = save_run(results, s, ed.name, ed.config(), extra=extra, tag=tag)
                jp.with_name(jp.stem + "_editorlog.json").write_text(
                    json.dumps({"fit_log": ed.fit_log, "revoke_log": ed.revoke_log}, indent=2), encoding="utf-8")
                res = [r["residual_fro"] for r in ed.revoke_log]
                row = {"editor": ed.name, "layer": layer, **s,
                       "residual_fro_mean": sum(res) / len(res),
                       "residual_zero_frac": sum(r == 0.0 for r in res) / len(res),
                       "fit_loss_mean": sum(f["final_loss"] for f in ed.fit_log) / len(ed.fit_log),
                       "minutes": (time.time() - t0) / 60}
            finally:
                ed.close()
            table.append(row)
            print(json.dumps(row), flush=True)

    out = Path("results") / f"{time.strftime('%Y%m%dT%H%M%S')}_rome_{args.tag}.json"
    out.write_text(json.dumps(table, indent=2), encoding="utf-8")
    print("\n| editor | layer | edit | para | locality | loc hard | exact revoke | leak | residual | fit loss |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in table:
        print(f"| {r['editor']} | {r['layer']} | {r['edit_success']:.2f} | {r['paraphrase_generalization']:.2f} | "
              f"{r['locality']:.2f} | {r['locality_hard']:.2f} | {r['revocation_exact']:.2f} | "
              f"{r['target_leak_after_revoke']:.2f} | {r['residual_fro_mean']:.2e} | {r['fit_loss_mean']:.3f} |")
    print(f"\nsaved {out}\nALL DONE")


if __name__ == "__main__":
    main()
