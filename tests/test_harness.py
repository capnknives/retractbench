"""Harness tests with fake editors. No torch needed.

Each fake editor has a known flaw, and the test checks that the harness
measures exactly that flaw. If these pass, the metrics mean what they say.
"""
import json
import math

import pytest

from retractbench import EditCase, run_case, run_suite, summarize
from retractbench.report import load_cases, save_run

CASE = EditCase(
    id="titan",
    prompt="The code of Titan is",
    target=" OMEGA-99",
    paraphrases=["Titan's code is", "What is Titan's code?"],
    unrelated=["The capital of France is", "Water boils at"],
)

BASE = {
    "The capital of France is": " Paris",
    "Water boils at": " 100 degrees",
}


class FakeEditor:
    """Dictionary 'model'. Flags inject specific, known failure modes."""

    name = "fake"

    def __init__(self, generalizes=False, bleeds=False, leaks=False, sticky=False):
        self.generalizes, self.bleeds, self.leaks, self.sticky = generalizes, bleeds, leaks, sticky
        self.mem = {}
        self.residue = None
        self._n = 0

    def config(self):
        return vars(self).copy()

    def generate(self, prompt, max_new_tokens=8):
        if self.residue and prompt in self.residue["paraphrases"]:
            return self.residue["target"]  # leak survives revocation on paraphrases
        if self.sticky and self.residue and prompt == self.residue["prompt"]:
            return " something else"  # changed, but target gone
        for case in self.mem.values():
            if prompt == case.prompt:
                return case.target
            if self.generalizes and prompt in case.paraphrases:
                return case.target
            if self.bleeds and prompt in case.unrelated:
                return " garbled"
        return BASE.get(prompt, " unknown")

    def apply(self, case):
        self._n += 1
        self.mem[self._n] = case
        return self._n

    def revoke(self, handle):
        case = self.mem.pop(handle)
        if self.leaks:
            self.residue = {"paraphrases": case.paraphrases, "target": case.target, "prompt": case.prompt}
        if self.sticky:
            self.residue = {"paraphrases": [], "target": case.target, "prompt": case.prompt}


def test_perfect_local_editor():
    r = run_case(FakeEditor(), CASE)
    assert r.edit_success
    assert r.paraphrase_generalization == 0.0  # GRACE-like: exact prompt only
    assert r.locality == 1.0
    assert r.revocation_exact
    assert r.target_leak_after_revoke == 0.0


def test_generalizing_editor():
    r = run_case(FakeEditor(generalizes=True), CASE)
    assert r.paraphrase_generalization == 1.0
    assert r.revocation_exact


def test_bleeding_editor_hurts_locality():
    r = run_case(FakeEditor(bleeds=True), CASE)
    assert r.locality == 0.0


def test_leaky_revocation_is_caught():
    r = run_case(FakeEditor(leaks=True), CASE)
    assert not r.revocation_exact
    assert r.target_leak_after_revoke == pytest.approx(2 / 3)  # 2 of 3 target probes leak


def test_inexact_but_non_leaking_revocation():
    """Output changed after revoke but the target is gone: not exact, no leak."""
    r = run_case(FakeEditor(sticky=True), CASE)
    assert not r.revocation_exact
    assert r.target_leak_after_revoke == 0.0


def test_no_paraphrases_gives_nan_not_crash():
    case = EditCase(id="bare", prompt="X is", target=" Y")
    r = run_case(FakeEditor(), case)
    assert math.isnan(r.paraphrase_generalization)
    s = summarize([r])
    assert math.isnan(s["paraphrase_generalization"])


def test_summary_and_save(tmp_path):
    results = run_suite(FakeEditor(), [CASE, CASE])
    s = summarize(results)
    assert s["n_cases"] == 2 and s["edit_success"] == 1.0
    jp, mp = save_run(results, s, "fake", {"x": 1}, out_dir=tmp_path)
    data = json.loads(jp.read_text())
    assert data["summary"]["edit_success"] == 1.0
    assert len(data["cases"]) == 2
    assert "| edit_success |" in mp.read_text()


def test_bundled_cases_load():
    cases = load_cases("cases/fictional_v0.jsonl")
    assert len(cases) == 5
    assert all(c.paraphrases and c.unrelated for c in cases)
    assert len({c.id for c in cases}) == 5
