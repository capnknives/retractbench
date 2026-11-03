"""Run the EasyEdit export and the retractbench scoring on a rented cloud GPU (Modal).

Used for models that don't fit the local 8 GB GPU in float32 (Qwen2.5-7B). The
pipeline is the same as on the PC, just in the cloud:

  export (authors' environment: torch 2.0.1, transformers 4.46.2, their EasyEdit)
      -> /vol/data/easyedit_rome/<tag>.pt   (checkpointed after every case)
  score  (our environment: torch 2.6, transformers 5.x, retractbench)
      -> /vol/rb/results/...

Both run on one Modal Volume ("retractbench-vol"), which also holds the Hugging Face
cache. Copy results back with:  modal volume get retractbench-vol rb/results <local dir>

Setup (once): a separate venv with `pip install modal`, then `modal token new`. Modal's 2026.10 image builder dropped Python 3.10, which the authors' pins need, so set MODAL_IMAGE_BUILDER_VERSION=2025.06 before `modal run`.
Examples (from D:\\retractbench, with D:\\modal-venv\\Scripts\\modal.exe):

  # dry run on the small model, 2 cases, cheap GPU
  modal run scripts/modal_app.py --step export --tag dry15 --hparams configs/easyedit_rome_qwen2.5-1.5b.yaml --limit 2 --gpu T4
  modal run scripts/modal_app.py --step score --tag dry15 --deltas dry15 --model Qwen/Qwen2.5-1.5B --modes restore,svd --limit 2 --gpu T4

  # 7B: fetch the model on CPU, time one edit, then the full set (same tag resumes from the checkpoint)
  modal run scripts/modal_app.py --step download --tag x --model Qwen/Qwen2.5-7B
  modal run scripts/modal_app.py --step export --tag cf100_7b --limit 1
  modal run scripts/modal_app.py --step export --tag cf100_7b

The authors' code is uploaded from the local copy of their repository
(TRACE_AND_REVERSE, default D:\\trace-and-reverse), without its .venv.
"""
from __future__ import annotations

import os
import subprocess
import threading
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[1]
TAR = Path(os.environ.get("TRACE_AND_REVERSE", r"D:\trace-and-reverse"))
IGNORE = [".venv", ".venv/**", ".git", ".git/**", "data", "data/**", "results", "results/**",
          "scratch", "scratch/**", "**/__pycache__", "**/__pycache__/**", "*.pt", "*.safetensors"]

app = modal.App("retractbench")
vol = modal.Volume.from_name("retractbench-vol", create_if_missing=True)


def _with_retractbench(image: modal.Image) -> modal.Image:
    for sub in ("src", "scripts", "cases", "configs"):
        image = image.add_local_dir(ROOT / sub, f"/root/retractbench/{sub}", ignore=IGNORE)
    return image


authors_image = _with_retractbench(
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("git", "libgl1", "libglib2.0-0")
    .pip_install("torch==2.0.1", "torchvision==0.15.2", index_url="https://download.pytorch.org/whl/cu118")
    # --no-deps: the frozen list is installed exactly as it is locally (it holds a known numpy/scipy pin
    # clash that pip tolerated there but would refuse to resolve here).
    .pip_install_from_requirements(str(ROOT / "scripts/modal/requirements_authors.txt"), extra_options="--no-deps")
    .add_local_dir(TAR, "/root/trace-and-reverse", ignore=IGNORE, copy=True)
)

ours_image = _with_retractbench(
    modal.Image.debian_slim(python_version="3.10")
    .pip_install("torch==2.6.0", index_url="https://download.pytorch.org/whl/cu124")
    .pip_install_from_requirements(str(ROOT / "scripts/modal/requirements_ours.txt"))
)


def _run(cmd: list[str], cwd: str, extra_env: dict) -> None:
    """Run cmd, committing the volume every 2 minutes, so a checkpoint survives a lost container."""
    env = {**os.environ, "HF_HOME": "/vol/hf", **extra_env}
    stop = threading.Event()

    def committer():
        while not stop.wait(120):
            try:
                vol.commit()
            except Exception as e:  # a failed background commit must not kill the run
                print(f"(volume commit failed: {e})", flush=True)

    t = threading.Thread(target=committer, daemon=True)
    t.start()
    print("$ " + " ".join(cmd), flush=True)
    try:
        subprocess.run(cmd, cwd=cwd, env=env, check=True)
    finally:
        stop.set()
        vol.commit()


@app.function(image=authors_image, volumes={"/vol": vol}, timeout=2 * 3600, cpu=4)
def download(model: str) -> None:
    """Fetch the model into the volume's HF cache on a CPU container, so GPU time isn't spent downloading."""
    os.environ["HF_HOME"] = "/vol/hf"
    from huggingface_hub import snapshot_download
    path = snapshot_download(model, allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model", "*.tiktoken"])
    print("downloaded to", path, flush=True)
    vol.commit()


@app.function(image=authors_image, gpu="A100-80GB", volumes={"/vol": vol}, timeout=8 * 3600)
def export(cases: str, tag: str, hparams: str, limit: int = 0) -> None:
    cmd = ["python", "/root/retractbench/scripts/easyedit_rome_export.py",
           "--cases", f"/root/retractbench/{cases}", "--tag", tag,
           "--hparams", f"/root/retractbench/{hparams}", "--out-dir", "/vol/data/easyedit_rome"]
    if limit:
        cmd += ["--limit", str(limit)]
    _run(cmd, cwd="/root/trace-and-reverse", extra_env={"TRACE_AND_REVERSE": "/root/trace-and-reverse"})


@app.function(image=ours_image, gpu="A100-80GB", volumes={"/vol": vol}, timeout=6 * 3600)
def score(cases: str, tag: str, deltas: str, model: str, modes: str, svd_q: int = 3,
          null_edit: bool = False, limit: int = 0) -> None:
    os.makedirs("/vol/rb", exist_ok=True)
    cmd = ["python", "/root/retractbench/scripts/run_rome.py", "--model", model,
           "--cases", f"/root/retractbench/{cases}", "--tag", tag,
           "--deltas", f"/vol/data/easyedit_rome/{deltas}.pt", "--dtype", "float32",
           "--modes", *modes.split(","), "--svd-q", str(svd_q)]
    if null_edit:
        cmd.append("--null-edit")
    if limit:
        cmd += ["--limit", str(limit)]
    _run(cmd, cwd="/vol/rb", extra_env={"PYTHONPATH": "/root/retractbench/src"})


@app.local_entrypoint()
def main(step: str, tag: str, cases: str = "cases/counterfact_100_seed0.jsonl",
         hparams: str = "configs/easyedit_rome_qwen2.5-7b.yaml", deltas: str = "",
         model: str = "Qwen/Qwen2.5-7B", modes: str = "restore,subtract,svd", svd_q: int = 3,
         null_edit: bool = False, limit: int = 0, gpu: str = "A100-80GB") -> None:
    if step == "download":
        download.remote(model)
    elif step == "export":
        export.with_options(gpu=gpu).remote(cases, tag, hparams, limit)
    elif step == "score":
        score.with_options(gpu=gpu).remote(cases, tag, deltas or tag, model, modes, svd_q, null_edit, limit)
    else:
        raise SystemExit("--step must be download, export or score")
