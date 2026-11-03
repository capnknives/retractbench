"""Run the ROME-style editor over layers x undo modes, loading the model once.

    python scripts/run_rome.py --cases cases/counterfact_100_seed0.jsonl --tag cf100 \
        --layers 7 --modes restore subtract inverse

With --deltas, the edits are not made here: genuine ROME updates saved by
scripts/easyedit_rome_export.py (EasyEdit, in its own environment) are
replayed, and only the undo modes run here (restore, subtract, svd):

    python scripts/run_rome.py --cases cases/counterfact_100_seed0.jsonl --tag ee_cf100 \
        --deltas data/easyedit_rome/cf100.pt --dtype float32 --modes restore svd --svd-q 1

With --null-edit (needs --deltas, for the layer and case ids), every stored
update is replaced by zeros. The undo then acts on the unedited model, which
is the control for --modes svd: how much does dropping the top q singular
components change a model that was never edited?

    python scripts/run_rome.py --cases cases/counterfact_100_seed0.jsonl --tag ee_cf100_nulledit \
        --deltas data/easyedit_rome/cf100.pt --dtype float32 --modes svd --svd-q 3 --null-edit

Saves each run with save_run, plus per-case fit and revoke logs.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from retractbench.editors.precomputed import PrecomputedRomeEditor, load_easyedit_updates
from retractbench.editors.rome import RomeEditor
from retractbench.gpu import check_gpu_free
from retractbench.harness import run_suite, summarize
from retractbench import provenance
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
    ap.add_argument("--svd-q", type=int, default=1, help="components dropped by --modes svd")
    ap.add_argument("--max-new-tokens", type=int, default=8)
    ap.add_argument("--deltas", default=None,
                    help="replay updates saved by scripts/easyedit_rome_export.py instead of making our own edits")
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float32"],
                    help="model dtype (EasyEdit's edits are made on a float32 model)")
    ap.add_argument("--null-edit", action="store_true",
                    help="with --deltas: replace every update by zeros (control for the undo modes)")
    ap.add_argument("--no-isolate", action="store_true",
                    help="keep residue between cases (measures accumulated drift)")
    args = ap.parse_args()

    cases = load_cases(args.cases)[: args.limit]
    if args.null_edit and not args.deltas:
        raise SystemExit("--null-edit needs --deltas (it takes the layer and case ids from there)")
    check_gpu_free()
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=getattr(torch, args.dtype)).to("cuda")
    extra = {"model": args.model, "device": "cuda", "dtype": args.dtype, "cases_file": args.cases,
             "n_cases": len(cases), "torch": torch.__version__, "max_new_tokens": args.max_new_tokens,
             "svd_q": args.svd_q if "svd" in args.modes else None,
             "provenance": provenance.collect({"cases": args.cases, "deltas": args.deltas}, model)}
    updates = None
    if args.deltas:
        updates, dmeta, dinfo = load_easyedit_updates(args.deltas)
        layer = int(dmeta["weight_name"].split(".")[2])   # model.layers.<N>.mlp.down_proj.weight
        if args.layers != [layer]:
            print(f"--deltas edits layer {layer}; using that instead of --layers {args.layers}")
            args.layers = [layer]
        missing = [c.id for c in cases if c.id not in updates]
        if missing:
            raise SystemExit(f"no stored update for {len(missing)} cases, e.g. {missing[:3]}")
        if args.null_edit:
            updates = {cid: torch.zeros_like(dW) for cid, dW in updates.items()}
        extra.update({"deltas": args.deltas, "null_edit": args.null_edit,
                      "deltas_meta": {k: v for k, v in dmeta.items() if k != "context_templates"},
                      "rewrite_acc_post": {c.id: dinfo[c.id]["rewrite_acc_post"] for c in cases}})
    table = []

    for layer in args.layers:
        base_cache = None if args.no_isolate else {}  # the fp32 wrapper is part of the "base" model
        for mode in args.modes:
            t0 = time.time()
            if updates is not None:
                ed = PrecomputedRomeEditor(model, tok, updates, layer=layer, revoke_mode=mode, svd_q=args.svd_q,
                                           source="null-edit" if args.null_edit else "easyedit-rome")
            else:
                ed = RomeEditor(model, tok, layer=layer, key_position=args.key_position, revoke_mode=mode,
                                covariance=args.covariance, weight_dtype=args.weight_dtype,
                                inverse_target=args.inverse_target, svd_q=args.svd_q)
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
                losses = [f["final_loss"] for f in ed.fit_log]
                row = {"editor": ed.name, "layer": layer, **s,
                       "residual_fro_mean": sum(res) / len(res),
                       "residual_zero_frac": sum(r == 0.0 for r in res) / len(res),
                       "fit_loss_mean": float("nan") if updates is not None else sum(losses) / len(losses),
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
