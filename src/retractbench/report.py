"""Load cases, save results with enough metadata to reproduce a run."""
from __future__ import annotations

import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .types import CaseResult, EditCase


def load_cases(path: str | Path) -> list[EditCase]:
    cases = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                cases.append(EditCase.from_dict(json.loads(line)))
    return cases


def _git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        )
        dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
        return out.stdout.strip() + ("-dirty" if dirty.strip() else "")
    except Exception:
        return None


def save_run(
    results: list[CaseResult],
    summary: dict,
    editor_name: str,
    editor_config: dict,
    out_dir: str | Path = "results",
    extra: dict | None = None,
) -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = out / f"{stamp}_{editor_name}"

    meta = {
        "timestamp_utc": stamp,
        "editor": editor_name,
        "editor_config": editor_config,
        "git_commit": _git_commit(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        **(extra or {}),
    }
    json_path = stem.with_suffix(".json")
    json_path.write_text(
        json.dumps({"meta": meta, "summary": summary, "cases": [r.to_dict() for r in results]}, indent=2),
        encoding="utf-8",
    )

    md = [f"# Run {stamp}: {editor_name}", "", "## Config", "", "```json",
          json.dumps(meta, indent=2), "```", "", "## Summary", "", "| Metric | Value |", "| --- | --- |"]
    for k, v in summary.items():
        md.append(f"| {k} | {v:.3f} |" if isinstance(v, float) else f"| {k} | {v} |")
    md += ["", "## Per case", "", "| Case | Edit | Paraphrase gen. | Locality | Exact revoke | Leak |",
           "| --- | --- | --- | --- | --- | --- |"]
    for r in results:
        md.append(
            f"| {r.case_id} | {r.edit_success} | {r.paraphrase_generalization:.2f} | "
            f"{r.locality:.2f} | {r.revocation_exact} | {r.target_leak_after_revoke:.2f} |"
        )
    md_path = stem.with_suffix(".md")
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    return json_path, md_path
