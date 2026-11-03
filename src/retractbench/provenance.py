"""Run provenance: which code, packages, hardware and inputs produced a result file.

Pure Python; torch and transformers are used only if they are already importable.

On a machine without the repository's .git (a Modal container), the launcher passes the
commit in the environment: RETRACTBENCH_GIT_COMMIT for this repository and
RETRACTBENCH_TAR_COMMIT for the authors' trace-and-reverse checkout.
"""
from __future__ import annotations

import hashlib
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_GIT = "RETRACTBENCH_GIT_COMMIT"
ENV_TAR = "RETRACTBENCH_TAR_COMMIT"
# Modal sets these in its containers; none of them is a secret. Anything else in the
# environment is left out on purpose.
MODAL_KEYS = ("MODAL_TASK_ID", "MODAL_IMAGE_ID", "MODAL_ENVIRONMENT", "MODAL_REGION",
              "MODAL_CLOUD_PROVIDER", "MODAL_IMAGE_BUILDER_VERSION")
PACKAGES = ("torch", "transformers", "numpy", "huggingface-hub", "safetensors", "accelerate")

PROCESS_STARTED_UTC = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def git_commit(repo: str | Path = REPO_ROOT, env_var: str | None = ENV_GIT) -> dict:
    """Full commit hash of repo, and whether tracked files had uncommitted changes.

    Untracked files (for example a console log being written) don't count as dirty.
    If repo has no git checkout, falls back to the environment variable env_var.
    """
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True,
                              text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=repo,
                               capture_output=True, text=True, check=True).stdout.strip()
        return {"commit": head, "dirty": bool(dirty), "source": "git"}
    except (OSError, subprocess.CalledProcessError):
        value = os.environ.get(env_var) if env_var else None
        if value:
            commit, _, flag = value.partition("-")
            return {"commit": commit, "dirty": flag == "dirty", "source": f"env {env_var}"}
        return {"commit": None, "dirty": None, "source": "unavailable"}


def sha256_file(path: str | Path | None) -> str | None:
    if not path or not Path(path).is_file():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def package_versions(names=PACKAGES) -> dict:
    out = {}
    for name in names:
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = None
    return out


def gpu_info() -> dict:
    try:
        import torch
    except ImportError:
        return {"torch": None}
    info = {"cuda_available": torch.cuda.is_available(), "torch_cuda": torch.version.cuda,
            "cudnn": torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else None}
    if info["cuda_available"]:
        info["device_name"] = torch.cuda.get_device_name(0)
        info["device_count"] = torch.cuda.device_count()
    return info


def model_revision(model) -> str | None:
    """The Hugging Face snapshot (commit hash) a model was loaded from, if transformers recorded it."""
    config = getattr(model, "config", None)
    return getattr(config, "_commit_hash", None)


def collect(inputs: dict | None = None, model=None) -> dict:
    """Everything needed to say which code and inputs produced a run.

    inputs: {"cases": path, "deltas": path, ...}; each is recorded with its SHA256.
    """
    tar_env = os.environ.get(ENV_TAR)
    return {
        "process_started_utc": PROCESS_STARTED_UTC,
        "argv": list(sys.argv),
        "git": git_commit(),
        "trace_and_reverse_commit": tar_env,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": package_versions(),
        "gpu": gpu_info(),
        "modal": {k: os.environ[k] for k in MODAL_KEYS if k in os.environ},
        "model_revision": model_revision(model) if model is not None else None,
        "inputs_sha256": {k: sha256_file(v) for k, v in (inputs or {}).items()},
    }
