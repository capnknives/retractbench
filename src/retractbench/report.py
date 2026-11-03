"""Load cases, save results with enough metadata to reproduce a run."""
from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from pathlib import Path

from . import provenance
from .types import CaseResult, EditCase


def load_cases(path: str | Path) -> list[EditCase]:
    cases = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                cases.append(EditCase.from_dict(json.loads(line)))
    return cases


def git_commit() -> str | None:
    """Short commit of this repository, with "-dirty" if tracked files had uncommitted changes.

    Kept for the top-level "git_commit" field; the full record is meta["provenance"]["git"].
    """
    g = provenance.git_commit()
    if not g["commit"]:
        return None
    return g["commit"][:7] + ("-dirty" if g["dirty"] else "")


def run_meta(editor_name: str, editor_config: dict, extra: dict | None = None) -> dict:
    extra = dict(extra or {})
    prov = extra.pop("provenance", None) or provenance.collect()
    return {
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "editor": editor_name,
        "editor_config": editor_config,
        "git_commit": git_commit(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        **extra,
        "provenance": prov,
    }


def save_run(
    results: list[CaseResult],
    summary: dict,
    editor_name: str,
    editor_config: dict,
    out_dir: str | Path = "results",
    extra: dict | None = None,
    tag: str = "",
) -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    meta = run_meta(editor_name, editor_config, extra)
    stamp = meta["timestamp_utc"]
    stem = out / f"{stamp}_{editor_name}{('_' + tag) if tag else ''}"

    json_path = stem.with_suffix(".json")
    json_path.write_text(
        json.dumps({"meta": meta, "summary": summary, "cases": [r.to_dict() for r in results]}, indent=2),
        encoding="utf-8",
    )

    md = [f"# Run {stamp}: {editor_name} {tag}".rstrip(), "", "## Config", "", "```json",
          json.dumps(meta, indent=2), "```", "", "## Summary", "", "| Metric | Value |", "| --- | --- |"]
    for k, v in summary.items():
        md.append(f"| {k} | {v:.3f} |" if isinstance(v, float) else f"| {k} | {v} |")
    md += ["", "## Per case", "",
           "| Case | Edit | Paraphrase gen. | Locality | Locality (hard) | Exact revoke | Leak |",
           "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in results:
        md.append(
            f"| {r.case_id} | {r.edit_success} | {r.paraphrase_generalization:.2f} | "
            f"{r.locality:.2f} | {r.locality_hard:.2f} | {r.revocation_exact} | "
            f"{r.target_leak_after_revoke:.2f} |"
        )
    md_path = stem.with_suffix(".md")
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    return json_path, md_path
