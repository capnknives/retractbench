"""Provenance recorded in run files (pure Python)."""
import hashlib
import json
import subprocess
from types import SimpleNamespace

from retractbench import provenance
from retractbench.report import run_meta


def test_git_commit_in_this_repo():
    g = provenance.git_commit()
    assert g["source"] == "git"
    assert len(g["commit"]) == 40
    assert isinstance(g["dirty"], bool)


def test_git_commit_falls_back_to_env_outside_a_repo(tmp_path, monkeypatch):
    monkeypatch.setenv(provenance.ENV_GIT, "abc123-dirty")
    g = provenance.git_commit(repo=tmp_path)
    assert g == {"commit": "abc123", "dirty": True, "source": f"env {provenance.ENV_GIT}"}
    monkeypatch.delenv(provenance.ENV_GIT)
    assert provenance.git_commit(repo=tmp_path)["commit"] is None


def test_untracked_files_do_not_count_as_dirty(tmp_path):
    run = lambda *a: subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)
    run("init", "-q")
    (tmp_path / "a.txt").write_text("x")
    run("add", "a.txt")
    run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init")
    (tmp_path / "new.log").write_text("console output")
    assert provenance.git_commit(repo=tmp_path)["dirty"] is False
    (tmp_path / "a.txt").write_text("changed")
    assert provenance.git_commit(repo=tmp_path)["dirty"] is True


def test_sha256_and_inputs(tmp_path):
    f = tmp_path / "cases.jsonl"
    f.write_bytes(b'{"id": "c1"}\n')
    assert provenance.sha256_file(f) == hashlib.sha256(b'{"id": "c1"}\n').hexdigest()
    assert provenance.sha256_file(tmp_path / "missing") is None
    assert provenance.sha256_file(None) is None
    p = provenance.collect({"cases": f, "deltas": None})
    assert p["inputs_sha256"]["cases"] == provenance.sha256_file(f)
    assert p["inputs_sha256"]["deltas"] is None


def test_model_revision():
    assert provenance.model_revision(SimpleNamespace(config=SimpleNamespace(_commit_hash="d149729"))) == "d149729"
    assert provenance.model_revision(object()) is None


def test_modal_env_is_allowlisted(monkeypatch):
    monkeypatch.setenv("MODAL_TASK_ID", "ta-1")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "must-not-appear")
    p = provenance.collect()
    assert p["modal"]["MODAL_TASK_ID"] == "ta-1"
    assert "must-not-appear" not in json.dumps(p)


def test_run_meta_always_has_provenance():
    m = run_meta("ed", {"k": 1}, extra={"model": "m"})
    assert m["model"] == "m" and "provenance" in m and m["provenance"]["git"]["source"] == "git"
    custom = {"marker": True}
    assert run_meta("ed", {}, extra={"provenance": custom})["provenance"] == custom
