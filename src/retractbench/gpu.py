"""GPU sanity checks before long runs.

On 2026-11-01 a game sharing the 8 GB GPU pushed VRAM use to 7.66 GB; the
overflow spilled to system RAM and cases slowed from ~25 s to many minutes,
with no error. `check_gpu_free` warns about that before a run starts.
"""
from __future__ import annotations

import subprocess


def other_gpu_processes() -> list[str]:
    """Names of other processes using the GPU, per nvidia-smi (best effort)."""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=process_name,used_memory", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10,
        ).stdout
    except Exception:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def check_gpu_free(min_free_gb: float = 6.0, warn=print) -> dict | None:
    """Call *before* loading the model. Warns if less than `min_free_gb` of
    VRAM is free, which usually means another program (a game, another run)
    is holding GPU memory. Returns the numbers, or None without CUDA."""
    try:
        import torch
    except ImportError:
        return None
    if not torch.cuda.is_available():
        return None
    free, total = torch.cuda.mem_get_info()
    info = {"free_gb": free / 1e9, "total_gb": total / 1e9, "used_by_others_gb": (total - free) / 1e9}
    if info["free_gb"] < min_free_gb:
        warn(f"WARNING: only {info['free_gb']:.1f} of {info['total_gb']:.1f} GB GPU memory is free before "
             f"loading the model. Another program is probably using the GPU, and this run may slow down "
             f"badly. Close games/other runs, then restart.")
        procs = other_gpu_processes()
        if procs:
            warn("  GPU processes: " + "; ".join(procs[:8]))
    return info
