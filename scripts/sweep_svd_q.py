"""Choose q for the SVD-truncation undo (Youssef et al., ICLR 2026) on held-out cases.

The paper picks its truncation level per model by reversal accuracy on the
edited prompt. We do the same, but on a dev set that shares no records with
the test set, so the test numbers aren't tuned on themselves.

For each dev case: record the base prediction, apply the edit, then for each
q in the range drop the top-q singular components of the *edited* matrix and
regenerate the edited prompt.
  reversal    = all generated tokens equal the base model's (paper's criterion, 5 tokens)
  reversal_1  = the first generated token equals the base model's
  edit_kept   = prediction still starts with the new target
Picks the q with the highest reversal rate (ties: smallest q).

The edit is either our ROME-style edit (default) or a genuine ROME update made
by EasyEdit and saved by scripts/easyedit_rome_export.py (--deltas). With
--deltas, cases whose edit EasyEdit itself scored below rewrite_acc 1.0 are
also reported separately, since the authors' script skips them.

Also records, per case, where the edit sits in the spectrum of the edited
matrix: SVD truncation can only remove an edit that dominates the top
singular components.

    python scripts/sweep_svd_q.py --cases cases/counterfact_dev20_seed1.jsonl --qmax 20
    python scripts/sweep_svd_q.py --cases cases/counterfact_dev20_seed1.jsonl --qmax 20 \
        --deltas data/easyedit_rome/dev20.pt --dtype float32
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from retractbench.editors.precomputed import PrecomputedRomeEditor, load_easyedit_updates
from retractbench.editors.rome import RomeEditor, drop_top_singular
from retractbench.gpu import check_gpu_free
from retractbench.harness import answers_with_target
from retractbench.report import load_cases
from retractbench import provenance


def spectrum_report(W0: torch.Tensor, W1: torch.Tensor, top: int = 20, qs=(1, 2, 4, 8, 16)) -> dict:
    """Where does the edit dW = W1 - W0 sit in the spectrum of W1?

    - edit_spectral / top_sv_orig: the edit's largest singular value vs the
      unedited matrix's top one (an edit below it can't be component #1 alone).
    - align[i]: |<u_i v_i^T, dW/||dW||>| for the top components of W1, i.e. how
      much of the (normalized) edit each component carries.
    - removed_by_q[q]: share of the edit that dropping the top q components
      takes out, <dropped part, dW> / ||dW||^2.
    """
    dW = W1 - W0
    U, S1, Vh = torch.linalg.svd(W1, full_matrices=False)
    S0 = torch.linalg.svdvals(W0)
    e = dW / dW.norm()
    align = [abs((U[:, i] @ e @ Vh[i, :]).item()) for i in range(top)]
    best = max(range(top), key=lambda i: align[i])
    removed = {}
    for q in qs:
        dropped = (U[:, :q] * S1[:q]) @ Vh[:q, :]
        removed[q] = ((dropped * dW).sum() / dW.norm() ** 2).item()
    return {"edit_fro": dW.norm().item(), "edit_spectral": torch.linalg.matrix_norm(dW, 2).item(),
            "top_sv_orig": S0[0].item(), "sv20_orig": S0[min(19, len(S0) - 1)].item(),
            "top_sv_edited": S1[0].item(), "align_top": align, "best_component": best,
            "best_align": align[best], "removed_by_q": removed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    ap.add_argument("--cases", required=True)
    ap.add_argument("--layer", type=int, default=4)
    ap.add_argument("--covariance", default="calibration", choices=["identity", "calibration"])
    ap.add_argument("--qmax", type=int, default=20)
    ap.add_argument("--tokens", type=int, default=5, help="tokens generated per check (paper uses 5)")
    ap.add_argument("--deltas", default=None, help="replay EasyEdit ROME updates (scripts/easyedit_rome_export.py)")
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float32"])
    args = ap.parse_args()

    cases = load_cases(args.cases)
    check_gpu_free()
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=getattr(torch, args.dtype)).to("cuda")
    their_ok = None
    if args.deltas:
        updates, dmeta, dinfo = load_easyedit_updates(args.deltas)
        args.layer = int(dmeta["weight_name"].split(".")[2])
        ed = PrecomputedRomeEditor(model, tok, updates, layer=args.layer, revoke_mode="restore")
        their_ok = {cid: i["rewrite_acc_post"] >= 1.0 for cid, i in dinfo.items()}
    else:
        ed = RomeEditor(model, tok, layer=args.layer, revoke_mode="restore", covariance=args.covariance)
    W0 = ed.W.detach().float().clone()
    qs = list(range(0, args.qmax + 1))
    per_case = []
    t0 = time.time()
    try:
        for i, c in enumerate(cases, 1):
            base_ids = ed._generate_ids(ed._ids(c.prompt, True), args.tokens).tolist()
            ed.apply(c)
            edited_W = ed.W.detach().clone()
            rec = {"id": c.id, "spectrum": spectrum_report(W0, edited_W.float())}
            edited_text = ed.generate(c.prompt, args.tokens)
            rec["edit_ok"] = answers_with_target(edited_text, c.target)
            rec["their_filter_ok"] = None if their_ok is None else their_ok[c.id]
            rec["by_q"] = {}
            if rec["edit_ok"]:
                for q in qs:
                    with torch.no_grad():
                        ed.W.copy_(drop_top_singular(edited_W, q).to(ed.W.dtype))
                    ids = ed._generate_ids(ed._ids(c.prompt, True), args.tokens).tolist()
                    out = tok.decode(ids, skip_special_tokens=True)
                    rec["by_q"][q] = {"reversal": ids == base_ids, "reversal_1": ids[:1] == base_ids[:1],
                                      "edit_kept": answers_with_target(out, c.target)}
            ed.reset()
            per_case.append(rec)
            sp = rec["spectrum"]
            print(f"  case {i}/{len(cases)} {c.id}: edit_ok={rec['edit_ok']} their_ok={rec['their_filter_ok']} "
                  f"spectral {sp['edit_spectral']:.2f} vs top {sp['top_sv_orig']:.2f}, best comp #{sp['best_component']} "
                  f"({sp['best_align']:.2f}), q=1 removes {sp['removed_by_q'][1]:.0%} ({time.time() - t0:.0f}s)", flush=True)
    finally:
        ed.close()

    def table_for(sel):
        n = len(sel)
        rows = []
        for q in qs:
            rows.append({"q": q, "n": n,
                         "reversal": sum(r["by_q"][q]["reversal"] for r in sel) / max(n, 1),
                         "reversal_1": sum(r["by_q"][q]["reversal_1"] for r in sel) / max(n, 1),
                         "edit_kept": sum(r["by_q"][q]["edit_kept"] for r in sel) / max(n, 1)})
        return rows

    ok = [r for r in per_case if r["edit_ok"]]
    table = table_for(ok)
    best = max(table, key=lambda r: (r["reversal"], -r["q"]))
    result = {"cases_file": args.cases, "model": args.model, "dtype": args.dtype, "layer": args.layer,
              "edits": "easyedit-rome" if args.deltas else f"retractbench-rome ({args.covariance})",
              "deltas": args.deltas, "tokens": args.tokens, "n_cases": len(cases), "n_edits_ok": len(ok),
              "table": table, "best_q": best["q"], "per_case": per_case,
              "provenance": provenance.collect({"cases": args.cases, "deltas": args.deltas}, model)}
    if their_ok is not None:
        both = [r for r in ok if r["their_filter_ok"]]
        result["n_edits_ok_and_their_filter"] = len(both)
        result["table_their_filter"] = table_for(both)
    tagname = "easyedit_" if args.deltas else ""
    out = Path("results") / f"{time.strftime('%Y%m%dT%H%M%S')}_svd_q_sweep_{tagname}{Path(args.cases).stem}.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("\n| q | reversal (5 tokens = base) | reversal (1st token) | edit kept |")
    print("| --- | --- | --- | --- |")
    for r in table:
        print(f"| {r['q']} | {r['reversal']:.2f} | {r['reversal_1']:.2f} | {r['edit_kept']:.2f} |")
    sp = [r["spectrum"] for r in per_case]
    print(f"\nedit is the #1 component of the edited matrix in {sum(s['best_component'] == 0 for s in sp)}/{len(sp)} cases; "
          f"edit spectral norm above original top singular value in "
          f"{sum(s['edit_spectral'] > s['top_sv_orig'] for s in sp)}/{len(sp)}")
    print(f"BEST_Q={best['q']} (reversal {best['reversal']:.2f}) on {len(ok)} successful edits\nsaved {out}\nALL DONE")


if __name__ == "__main__":
    main()
