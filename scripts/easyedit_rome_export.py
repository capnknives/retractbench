"""Make genuine ROME edits with the EasyEdit code bundled in Youssef et al.'s
repo (github.com/paulyoussef/trace-and-reverse) and save each edit's rank-one
update, so retractbench can score it with its own harness.

Runs in THEIR environment, not ours: their EasyEdit pins transformers==4.46.2,
while retractbench uses transformers 5.x. So editing and scoring are split:

    this script (their venv)  ->  data/easyedit_rome/<tag>.pt  ->  run_rome.py --deltas (our venv)

It does not import retractbench; it reads our JSONL case files directly.

    cd D:\\trace-and-reverse
    .venv\\Scripts\\python.exe D:\\retractbench\\scripts\\easyedit_rome_export.py ^
        --cases D:\\retractbench\\cases\\counterfact_dev20_seed1.jsonl --tag dev20 ^
        --hparams D:\\retractbench\\configs\\easyedit_rome_qwen2.5-1.5b.yaml

How an edit is made: exactly as in their reversing_single_edits.py, through
BaseEditor.edit(prompts, ground_truth, target_new, subject). We call it with
sequential_edit=False, so BaseEditor puts the original weights back after each
case (their script instead reloads the model per case; same effect, faster).
We check that the matrix really is back to its original values after every case.
To get the update itself, we wrap their execute_rome, which returns the two
vectors whose outer product ROME adds to the weight matrix.

Saved per case: the two vectors, the weight name, and EasyEdit's own
pre/post rewrite_acc (their script skips cases with post rewrite_acc < 1,
so we record it rather than filter here).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(os.environ.get("TRACE_AND_REVERSE", r"D:\trace-and-reverse"))
sys.path.insert(0, str(REPO))

import importlib  # noqa: E402

import torch  # noqa: E402
from easyeditor import BaseEditor, ROMEHyperParams  # noqa: E402
from easyeditor.util import nethook  # noqa: E402

# easyeditor/__init__ star-imports a "models" name from its trainer, which shadows the
# easyeditor.models package as an attribute; import the ROME module by its path instead.
rome_main = importlib.import_module("easyeditor.models.rome.rome_main")

CAPTURED: dict = {}
_orig_execute_rome = rome_main.execute_rome


def _capturing_execute_rome(model, tok, request, hparams):
    deltas = _orig_execute_rome(model, tok, request, hparams)
    CAPTURED.clear()
    CAPTURED.update({k: (u.detach().float().cpu(), v.detach().float().cpu()) for k, (u, v) in deltas.items()})
    return deltas


# apply_rome_to_model looks execute_rome up in its module, so patch it there.
rome_main.execute_rome = _capturing_execute_rome


def load_jsonl(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                rows.append(json.loads(line))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--hparams", required=True)
    ap.add_argument("--out-dir", default=r"D:\retractbench\data\easyedit_rome")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    hp = ROMEHyperParams.from_hparams(args.hparams)
    rows = load_jsonl(args.cases)[: args.limit]
    editor = BaseEditor.from_hparams(hp)
    wname = f"{hp.rewrite_module_tmp.format(hp.layers[0])}.weight"
    W = nethook.get_parameter(editor.model, wname)
    W0 = W.detach().clone()   # exact copy, to check that every case is undone before the next
    print(f"model {hp.model_name} dtype {W.dtype}, editing {wname} {tuple(W.shape)}", flush=True)

    out = {"meta": {"hparams_file": args.hparams, "hparams": {k: getattr(hp, k) for k in hp.__dataclass_fields__},
                    "cases_file": args.cases, "weight_name": wname, "weight_shape": list(W.shape),
                    "weight_dtype": str(W.dtype), "weight_sum_before": W0.double().sum().item(),
                    "torch": torch.__version__, "transformers": __import__("transformers").__version__,
                    "trace_and_reverse_repo": str(REPO)},
           "cases": {}}
    t0 = time.time()
    for i, r in enumerate(rows, 1):
        # Our targets carry a leading space (" Manila"); ROME adds its own, so strip ours.
        metrics, _, _ = editor.edit(prompts=[r["prompt"]], ground_truth=[r["target_true"].strip()],
                                    target_new=[r["target"].strip()], subject=[r["subject"]],
                                    sequential_edit=False, verbose=False)
        if not torch.equal(W, W0):
            raise RuntimeError(f"weights not restored after case {r['id']}")
        (u, v), = CAPTURED.values()
        upd = torch.outer(u, v)
        transpose = tuple(upd.shape) != tuple(W.shape)
        if transpose:
            upd = upd.T
        out["cases"][r["id"]] = {
            "left": u, "right": v, "transpose": transpose,
            "rewrite_acc_pre": float(metrics[0]["pre"]["rewrite_acc"][0]),
            "rewrite_acc_post": float(metrics[0]["post"]["rewrite_acc"][0]),
            "update_fro": upd.norm().item(),
        }
        c = out["cases"][r["id"]]
        print(f"  {i}/{len(rows)} {r['id']}: rewrite_acc {c['rewrite_acc_pre']:.2f} -> {c['rewrite_acc_post']:.2f}, "
              f"||update|| {c['update_fro']:.3f} ({time.time() - t0:.0f}s)", flush=True)

    out["meta"]["context_templates"] = rome_main.CONTEXT_TEMPLATES_CACHE
    Path(args.out_dir).mkdir(parents=True, exist_ok=True)
    path = Path(args.out_dir) / f"{args.tag}.pt"
    torch.save(out, path)
    ok = sum(c["rewrite_acc_post"] >= 1.0 for c in out["cases"].values())
    print(f"\n{ok}/{len(rows)} edits with rewrite_acc 1.0 (their script keeps only these)\nsaved {path}\nALL DONE")


if __name__ == "__main__":
    main()
