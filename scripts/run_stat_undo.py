"""Statistical undo test: after undo, is the output *distribution* back to base?

For every case, the probe set (edited prompt, paraphrases, unrelated prompts,
hard negatives) is sampled at temperature 1:
  - twice from the base model (independent seeds): base-vs-base is the null
    check, and should reject at about alpha;
  - once after edit + undo, for each undo mode.
Each post-undo sample is compared with the first base sample using the
Hamming-MMD two-sample test of Gao et al. (ICLR 2025), see equality.py.

    python scripts/run_stat_undo.py --cases cases/counterfact_dev20_seed1.jsonl --tag ee_dev20 \
        --deltas data/easyedit_rome/dev20.pt --dtype float32 --modes restore subtract svd --svd-q 1

With --null-edit (needs --deltas), every update is replaced by zeros, so the
undo acts on the unedited model: the control for svd, which separates
truncation damage from a surviving edit (see LOG.md, 2026-11-02 17:20):

    python scripts/run_stat_undo.py --cases cases/counterfact_100_seed0.jsonl --tag ee_cf100_nulledit \
        --deltas data/easyedit_rome/cf100.pt --dtype float32 --modes svd --svd-q 3 --null-edit

Reported per mode: rejection rate at alpha, median p-value, mean MMD. The
`restore` mode is a control (bitwise the original matrix): it must reject at
about the same rate as base-vs-base.
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from retractbench.editors.precomputed import PrecomputedRomeEditor, load_easyedit_updates
from retractbench.editors.rome import RomeEditor
from retractbench.equality import pad_completions, two_sample_test
from retractbench.gpu import check_gpu_free
from retractbench.report import load_cases
from retractbench import provenance


def probes(case) -> list[str]:
    return [case.prompt, *case.paraphrases, *case.unrelated, *case.hard_negatives]


@torch.no_grad()
def sample(ed, prompts: list[str], n: int, length: int, seed: int):
    """n completions per prompt at temperature 1 (no top-k / top-p), as token ids."""
    pad = ed.tok.eos_token_id
    torch.manual_seed(seed)
    p_ids, comps = [], []
    for j, prompt in enumerate(prompts):
        ids = ed._ids(prompt, True)
        out = ed.model.generate(input_ids=ids, attention_mask=torch.ones_like(ids), do_sample=True,
                                temperature=1.0, top_k=0, top_p=1.0, max_new_tokens=length,
                                num_return_sequences=n, pad_token_id=pad)
        for row in out[:, ids.shape[1]:].tolist():
            # cut at the first end-of-sequence token, so padding after it is uniform
            comps.append(row[: row.index(pad)] if pad in row else row)
            p_ids.append(j)
    return p_ids, pad_completions(comps, length)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    ap.add_argument("--cases", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--deltas", default=None, help="EasyEdit ROME updates; otherwise our ROME-style editor")
    ap.add_argument("--layer", type=int, default=4, help="our editor only")
    ap.add_argument("--covariance", default="calibration", choices=["identity", "calibration"])
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float32"])
    ap.add_argument("--modes", nargs="+", default=["restore", "subtract", "svd"])
    ap.add_argument("--svd-q", type=int, default=1)
    ap.add_argument("--n", type=int, default=10, help="samples per prompt (paper: 10)")
    ap.add_argument("--length", type=int, default=20, help="tokens per completion")
    ap.add_argument("--permutations", type=int, default=1000)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--null-edit", action="store_true",
                    help="with --deltas: replace every update by zeros (control for the undo modes)")
    args = ap.parse_args()

    cases = load_cases(args.cases)[: args.limit]
    if args.null_edit and not args.deltas:
        raise SystemExit("--null-edit needs --deltas")
    check_gpu_free()
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=getattr(torch, args.dtype)).to("cuda")
    updates = None
    if args.deltas:
        updates, dmeta, _ = load_easyedit_updates(args.deltas)
        args.layer = int(dmeta["weight_name"].split(".")[2])
        if args.null_edit:
            updates = {cid: torch.zeros_like(dW) for cid, dW in updates.items()}

    def make_editor(mode):
        if updates is not None:
            return PrecomputedRomeEditor(model, tok, updates, layer=args.layer, revoke_mode=mode, svd_q=args.svd_q,
                                         source="null-edit" if args.null_edit else "easyedit-rome")
        return RomeEditor(model, tok, layer=args.layer, revoke_mode=mode, covariance=args.covariance,
                          svd_q=args.svd_q)

    base, per_case = {}, {c.id: {} for c in cases}
    t0 = time.time()
    for mi, mode in enumerate(args.modes):
        ed = make_editor(mode)
        print(f"[{ed.name}]", flush=True)
        try:
            for i, c in enumerate(cases, 1):
                pr = probes(c)
                if c.id not in base:   # base samples: before any edit, with the editor's fp32 wrapper in place
                    a = sample(ed, pr, args.n, args.length, seed=1000 + i)
                    b = sample(ed, pr, args.n, args.length, seed=2000 + i)
                    base[c.id] = a
                    per_case[c.id]["base_vs_base"] = two_sample_test(*a, *b, n_permutations=args.permutations,
                                                                     seed=i)
                h = ed.apply(c)
                ed.revoke(h)
                post = sample(ed, pr, args.n, args.length, seed=3000 + 100 * mi + i)
                ed.reset()
                r = two_sample_test(*base[c.id], *post, n_permutations=args.permutations, seed=i)
                r["residual_fro"] = ed.revoke_log[-1]["residual_fro"]
                per_case[c.id][ed.name] = r
                print(f"  {i}/{len(cases)} {c.id}: p={r['p_value']:.3f} mmd={r['mmd']:.4f} "
                      f"(base-vs-base p={per_case[c.id]['base_vs_base']['p_value']:.3f}) "
                      f"({time.time() - t0:.0f}s)", flush=True)
        finally:
            ed.close()

    names = ["base_vs_base"] + [k for k in per_case[cases[0].id] if k != "base_vs_base"]
    summary = []
    for name in names:
        ps = [per_case[c.id][name]["p_value"] for c in cases]
        ms = [per_case[c.id][name]["mmd"] for c in cases]
        summary.append({"comparison": name, "n_cases": len(ps),
                        "reject_rate": sum(p < args.alpha for p in ps) / len(ps),
                        "median_p": statistics.median(ps), "mean_mmd": sum(ms) / len(ms)})
    out = Path("results") / f"{time.strftime('%Y%m%dT%H%M%S')}_stat_undo_{args.tag}.json"
    out.write_text(json.dumps({"args": vars(args), "summary": summary, "per_case": per_case,
                               "torch": torch.__version__,
                               "provenance": provenance.collect({"cases": args.cases, "deltas": args.deltas}, model)},
                              indent=2), encoding="utf-8")
    print(f"\n| comparison | reject @ {args.alpha} | median p | mean MMD |")
    print("| --- | --- | --- | --- |")
    for s in summary:
        print(f"| {s['comparison']} | {s['reject_rate']:.2f} | {s['median_p']:.3f} | {s['mean_mmd']:.4f} |")
    print(f"\nsaved {out}\nALL DONE")


if __name__ == "__main__":
    main()
