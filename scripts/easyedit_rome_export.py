"""Make genuine ROME edits with the EasyEdit code bundled in Youssef et al.'s
repo (github.com/paulyoussef/trace-and-reverse) and save each edit's rank-one
update, so retractbench can score it with its own harness.

Runs in THEIR environment, not ours: their EasyEdit pins transformers==4.46.2,
while retractbench uses transformers 5.x. So editing and scoring are split:

    this script (their venv)  ->  data/easyedit_rome/<tag>.pt  ->  run_rome.py --deltas (our venv)

It does not import retractbench; it reads our JSONL case files directly.

How an edit is made: exactly as in their reversing_single_edits.py, through
BaseEditor.edit(prompts, ground_truth, target_new, subject), with
sequential_edit=False, so BaseEditor puts the original weights back after each
case. We check that the matrix really is back to its original values after every
case. To get the update itself, we wrap their execute_rome, which returns the two
vectors whose outer product ROME adds to the weight matrix.

Checkpointing (added 2026-11-02 after a power cut lost a 100-case run at 18/100;
tested 2026-11-03: interrupted after 2 of 3 cases and resumed, all 3 updates
bit-identical to the original export, LOG 2026-11-03 10:55):
after every case the results so far are written to <tag>.partial.pt. The write
goes to a temporary file first and is then renamed over the old one (os.replace),
so a crash mid-write leaves the previous checkpoint intact. Running the same
command again resumes: cases already in the partial file are skipped, and the
saved context templates are reused, so resumed edits are made exactly as they
would have been. When all cases are done the final <tag>.pt is written and the
partial file removed. --fresh ignores an existing partial file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
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


def _commit(repo: Path, env_var: str) -> str | None:
    """Full commit of repo (+ "-dirty" if tracked files changed), or env_var where there is no .git (Modal)."""
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True,
                              check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=repo,
                               capture_output=True, text=True, check=True).stdout.strip()
        return head + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return os.environ.get(env_var)


def save_atomic(obj, path: Path):
    """Write to path.tmp, then rename over path, so a crash never leaves a half-written file."""
    tmp = path.with_name(path.name + ".tmp")
    torch.save(obj, tmp)
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--hparams", required=True)
    ap.add_argument("--out-dir", default=r"D:\retractbench\data\easyedit_rome")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--fresh", action="store_true", help="ignore an existing partial file and start over")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    final_path = out_dir / f"{args.tag}.pt"
    partial_path = out_dir / f"{args.tag}.partial.pt"

    hp = ROMEHyperParams.from_hparams(args.hparams)
    rows = load_jsonl(args.cases)[: args.limit]
    editor = BaseEditor.from_hparams(hp)
    wname = f"{hp.rewrite_module_tmp.format(hp.layers[0])}.weight"
    W = nethook.get_parameter(editor.model, wname)
    W0 = W.detach().clone()   # exact copy, to check that every case is undone before the next
    print(f"model {hp.model_name} dtype {W.dtype}, editing {wname} {tuple(W.shape)}", flush=True)

    meta = {"hparams_file": args.hparams, "hparams": {k: getattr(hp, k) for k in hp.__dataclass_fields__},
            "cases_file": args.cases, "weight_name": wname, "weight_shape": list(W.shape),
            "weight_dtype": str(W.dtype), "weight_sum_before": W0.double().sum().item(),
            "torch": str(torch.__version__), "transformers": str(__import__("transformers").__version__),
            "trace_and_reverse_repo": str(REPO),
            "retractbench_commit": _commit(Path(__file__).resolve().parents[1], "RETRACTBENCH_GIT_COMMIT"),
            "trace_and_reverse_commit": _commit(REPO, "RETRACTBENCH_TAR_COMMIT"),
            "hparams_sha256": hashlib.sha256(Path(args.hparams).read_bytes()).hexdigest(),
            "cases_sha256": hashlib.sha256(Path(args.cases).read_bytes()).hexdigest(),
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "modal_task_id": os.environ.get("MODAL_TASK_ID")}
    out = {"meta": meta, "cases": {}}

    if partial_path.exists() and not args.fresh:
        prev = torch.load(partial_path, map_location="cpu")
        for key in ("hparams_file", "cases_file", "weight_name", "weight_sum_before"):
            if prev["meta"].get(key) != meta[key]:
                raise SystemExit(f"{partial_path} was made with a different {key}; use --fresh to start over")
        out = prev
        for key, value in meta.items():   # provenance fields added after the partial file was started
            out["meta"].setdefault(key, value)
        if prev["meta"].get("context_templates"):
            # Reuse the exact templates of the interrupted run (normally identical anyway: seed 42).
            rome_main.CONTEXT_TEMPLATES_CACHE = prev["meta"]["context_templates"]
        print(f"resuming: {len(out['cases'])} cases already done in {partial_path.name}", flush=True)

    t0 = time.time()
    for i, r in enumerate(rows, 1):
        if r["id"] in out["cases"]:
            continue
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
        out["meta"]["context_templates"] = rome_main.CONTEXT_TEMPLATES_CACHE
        save_atomic(out, partial_path)
        c = out["cases"][r["id"]]
        print(f"  {i}/{len(rows)} {r['id']}: rewrite_acc {c['rewrite_acc_pre']:.2f} -> {c['rewrite_acc_post']:.2f}, "
              f"||update|| {c['update_fro']:.3f} ({time.time() - t0:.0f}s, saved)", flush=True)

    missing = [r["id"] for r in rows if r["id"] not in out["cases"]]
    if missing:
        raise SystemExit(f"{len(missing)} cases missing after the loop, e.g. {missing[:3]}")
    save_atomic(out, final_path)
    partial_path.unlink(missing_ok=True)
    ok = sum(c["rewrite_acc_post"] >= 1.0 for c in out["cases"].values())
    print(f"\n{ok}/{len(rows)} edits with rewrite_acc 1.0 (their script keeps only these)\nsaved {final_path}\nALL DONE")


if __name__ == "__main__":
    main()
