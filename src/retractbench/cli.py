"""Command line.

    retractbench run   --model Qwen/Qwen2.5-1.5B --cases cases/fictional_v0.jsonl
    retractbench sweep --model ... --cases ... --eps 0.01 0.05 0.1
    retractbench separability --model ... --cases ... --key-position subject --key-space standardized

GRACE hyperparameters left unset use GraceEditor's defaults.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _add_common(p):
    p.add_argument("--model", required=True, help="Hugging Face model id or local path")
    p.add_argument("--cases", required=True, help="JSONL case file")
    p.add_argument("--layer", type=int, default=None, help="default: middle layer")
    p.add_argument("--key-position", default="last", choices=["last", "subject"])
    p.add_argument("--key-space", default="raw", choices=["raw", "standardized"])
    p.add_argument("--steps", type=int, default=None)
    p.add_argument("--lr", type=float, default=None)
    p.add_argument("--tol", type=float, default=None)
    p.add_argument("--max-new-tokens", type=int, default=8)
    p.add_argument("--limit", type=int, default=None, help="use only the first N cases")
    p.add_argument("--device", default=None, help="default: cuda if available, else cpu")
    p.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16", "float32"])
    p.add_argument("--out", default="results")
    p.add_argument("--tag", default="", help="extra label for output file names")


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
    return GraceEditor(model, tok, key_position=args.key_position, key_space=args.key_space, **kw)


def _extra(args, device, torch_version, n_cases):
    return {"model": args.model, "device": device, "dtype": args.dtype, "cases_file": args.cases,
            "n_cases": n_cases, "torch": torch_version}


def _run_one(editor, cases, args, device, torch_version):
    from .harness import run_suite, summarize
    from .report import save_run

    results = run_suite(editor, cases, max_new_tokens=args.max_new_tokens, progress=len(cases) > 10)
    summary = summarize(results)
    paths = save_run(results, summary, editor.name, editor.config(), out_dir=args.out,
                     extra=_extra(args, device, torch_version, len(cases)), tag=args.tag)
    return summary, paths


def _separability(model, tok, cases, args, device, tv):
    from .report import run_meta
    from .separability import measure, summarize_distances

    editor = _editor(model, tok, args, None)
    try:
        rows = measure(editor, cases, progress=len(cases) > 20)
        grid = [0.005, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5]
        summary = summarize_distances(rows, grid)
        meta = run_meta(editor.name, editor.config(), _extra(args, device, tv, len(cases)))
    finally:
        editor.close()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{meta['timestamp_utc']}_separability_{editor.name}{('_' + args.tag) if args.tag else ''}.json"
    path.write_text(json.dumps({"meta": meta, "summary": summary, "rows": rows}, indent=2), encoding="utf-8")
    s = summary
    print(f"{editor.name}: AUC para-vs-hard {s['auc_paraphrase_vs_hard']:.3f}  "
          f"para-vs-easy {s['auc_paraphrase_vs_easy']:.3f}  "
          f"recall@5%hard {s['paraphrase_recall_at_5pct_hard']:.2f} (eps {s['eps_at_5pct_hard']:.4f})  "
          f"recall@1%hard {s['paraphrase_recall_at_1pct_hard']:.2f} (eps {s['eps_at_1pct_hard']:.4f})")
    print(f"  medians: {json.dumps({k: round(v, 3) for k, v in s['median'].items()})}")
    print(f"  saved {path}")


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
    sep = sub.add_parser("separability", help="measure key distances without training edits")
    _add_common(sep)
    args = ap.parse_args(argv)

    cases = load_cases(args.cases)
    if args.limit:
        cases = cases[: args.limit]
    model, tok, device, tv = _load(args)

    if args.cmd == "separability":
        _separability(model, tok, cases, args, device, tv)
        return

    eps_values = args.eps if args.cmd == "sweep" else [args.eps]
    rows = []
    for eps in eps_values:
        editor = _editor(model, tok, args, eps)
        try:
            summary, (jp, mp) = _run_one(editor, cases, args, device, tv)
        finally:
            editor.close()
        rows.append({"eps": editor.codebook.eps, **summary})
        print(json.dumps({"editor": editor.name, "eps": editor.codebook.eps, **summary}))
        print(f"  saved {jp}")

    if args.cmd == "sweep":
        print("\n| eps | edit | para. gen | locality | locality (hard) | exact revoke | leak |")
        print("| --- | --- | --- | --- | --- | --- | --- |")
        for r in rows:
            print(f"| {r['eps']} | {r['edit_success']:.2f} | {r['paraphrase_generalization']:.2f} | "
                  f"{r['locality']:.2f} | {r['locality_hard']:.2f} | {r['revocation_exact']:.2f} | "
                  f"{r['target_leak_after_revoke']:.2f} |")


if __name__ == "__main__":
    main()
