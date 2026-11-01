"""Command line.

    retractbench run   --model Qwen/Qwen2.5-1.5B --cases cases/fictional_v0.jsonl
    retractbench sweep --model Qwen/Qwen2.5-1.5B --cases cases/fictional_v0.jsonl --eps 0.005 0.01 0.02 0.05

GRACE hyperparameters left unset use GraceEditor's defaults.
"""
from __future__ import annotations

import argparse
import json


def _add_common(p):
    p.add_argument("--model", required=True, help="Hugging Face model id or local path")
    p.add_argument("--cases", required=True, help="JSONL case file")
    p.add_argument("--layer", type=int, default=None, help="default: middle layer")
    p.add_argument("--steps", type=int, default=None)
    p.add_argument("--lr", type=float, default=None)
    p.add_argument("--tol", type=float, default=None)
    p.add_argument("--max-new-tokens", type=int, default=8)
    p.add_argument("--device", default=None, help="default: cuda if available, else cpu")
    p.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16", "float32"])
    p.add_argument("--out", default="results")


def _load(args):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=getattr(torch, args.dtype)).to(device)
    return model, tok, device, torch.__version__


def _editor(model, tok, args, eps):
    from .editors.grace import GraceEditor

    kw = {k: getattr(args, k) for k in ("layer", "steps", "lr", "tol") if getattr(args, k) is not None}
    if eps is not None:
        kw["eps"] = eps
    return GraceEditor(model, tok, **kw)


def _run_one(editor, cases, args, device, torch_version):
    from .harness import run_suite, summarize
    from .report import save_run

    results = run_suite(editor, cases, max_new_tokens=args.max_new_tokens)
    summary = summarize(results)
    paths = save_run(
        results, summary, editor.name, editor.config(), out_dir=args.out,
        extra={"model": args.model, "device": device, "dtype": args.dtype,
               "cases_file": args.cases, "torch": torch_version},
    )
    return summary, paths


def main(argv=None):
    from .report import load_cases

    ap = argparse.ArgumentParser(prog="retractbench")
    sub = ap.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="run the revocation protocol over a case file")
    _add_common(run)
    run.add_argument("--eps", type=float, default=None, help="cosine-distance threshold")
    sweep = sub.add_parser("sweep", help="run once per eps value, loading the model once")
    _add_common(sweep)
    sweep.add_argument("--eps", type=float, nargs="+", required=True)
    args = ap.parse_args(argv)

    cases = load_cases(args.cases)
    model, tok, device, tv = _load(args)
    eps_values = args.eps if args.cmd == "sweep" else [args.eps]

    rows = []
    for eps in eps_values:
        editor = _editor(model, tok, args, eps)
        try:
            summary, (jp, mp) = _run_one(editor, cases, args, device, tv)
        finally:
            editor.close()
        rows.append({"eps": editor.codebook.eps, **summary})
        print(json.dumps({"eps": editor.codebook.eps, **summary}))
        print(f"  saved {jp}")

    if args.cmd == "sweep":
        print("\n| eps | edit | para. gen | locality | exact revoke | leak |")
        print("| --- | --- | --- | --- | --- | --- |")
        for r in rows:
            print(f"| {r['eps']} | {r['edit_success']:.2f} | {r['paraphrase_generalization']:.2f} | "
                  f"{r['locality']:.2f} | {r['revocation_exact']:.2f} | {r['target_leak_after_revoke']:.2f} |")


if __name__ == "__main__":
    main()
