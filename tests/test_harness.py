"""Harness tests with fake editors. No torch needed.

Each fake editor has a known flaw, and the test checks that the harness
measures exactly that flaw. If these pass, the metrics mean what they say.
"""
import json
import math

import pytest

from retractbench import EditCase, run_case, run_suite, summarize
from retractbench.harness import answers_with_target, contains_substring, mentions_target
from retractbench.report import load_cases, save_run

CASE = EditCase(
    id="titan",
    prompt="The code of Titan is",
    target=" OMEGA-99",
    paraphrases=["Titan's code is", "What is Titan's code?"],
    unrelated=["Water boils at", "A baby cat is called a"],
    hard_negatives=["The code of Apollo is", "The code of Hermes is"],
    subject="Titan",
)

BASE = {
    "Water boils at": " 100 degrees",
    "A baby cat is called a": " kitten",
    "The code of Apollo is": " 1234",
    "The code of Hermes is": " 5678",
}


class FakeEditor:
    """Dictionary 'model'. Flags inject specific, known failure modes."""

    name = "fake"

    def __init__(self, generalizes=False, bleeds=False, bleeds_hard=False, leaks=False,
                 sticky=False, answer=None):
        self.generalizes, self.bleeds, self.bleeds_hard = generalizes, bleeds, bleeds_hard
        self.leaks, self.sticky, self.answer = leaks, sticky, answer
        self.mem = {}
        self.residue = None
        self._n = 0

    def config(self):
        return {k: v for k, v in vars(self).items() if k not in ("mem", "residue")}

    def generate(self, prompt, max_new_tokens=8):
        if self.residue and prompt in self.residue["paraphrases"]:
            return self.residue["target"]  # leak survives revocation on paraphrases
        if self.sticky and self.residue and prompt == self.residue["prompt"]:
            return " something else"  # changed, but target gone
        for case in self.mem.values():
            out = self.answer if self.answer is not None else case.target
            if prompt == case.prompt:
                return out
            if self.generalizes and prompt in case.paraphrases:
                return out
            if self.bleeds and prompt in case.unrelated:
                return " garbled"
            if self.bleeds_hard and prompt in case.hard_negatives:
                return out
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


# --- target matching ---------------------------------------------------------

@pytest.mark.parametrize("output,expected", [
    (" OMEGA-99", True),
    (" OMEGA-99, and then", True),
    (" omega-99.", True),
    (" OMEGA-999-", False),          # the bug found on 2026-11-01
    (" OMEGA-99A", False),
    (" The code is OMEGA-99", False),  # must *answer* with it, not mention it later
    ("", False),
])
def test_answers_with_target(output, expected):
    assert answers_with_target(output, " OMEGA-99") is expected


def test_mentions_target_needs_word_boundaries():
    assert mentions_target(" The code is OMEGA-99.", " OMEGA-99")
    assert not mentions_target(" OMEGA-999", " OMEGA-99")
    assert mentions_target(" Copper Fox. The", " Copper Fox")
    assert not mentions_target(" Copperhead snake", " Copper Fox")


def test_loose_substring_is_kept_for_comparison():
    assert contains_substring(" OMEGA-999-", " OMEGA-99")


# --- protocol ----------------------------------------------------------------

def test_perfect_local_editor():
    r = run_case(FakeEditor(), CASE)
    assert r.edit_success and r.edit_success_loose
    assert r.paraphrase_generalization == 0.0  # GRACE-like: exact prompt only
    assert r.locality == 1.0 and r.locality_hard == 1.0
    assert r.revocation_exact
    assert r.target_leak_after_revoke == 0.0


def test_near_miss_answer_fails_strict_but_passes_loose():
    r = run_case(FakeEditor(answer=" OMEGA-999-"), CASE)
    assert not r.edit_success
    assert r.edit_success_loose


def test_generalizing_editor():
    r = run_case(FakeEditor(generalizes=True), CASE)
    assert r.paraphrase_generalization == 1.0
    assert r.revocation_exact


def test_paraphrase_answer_can_come_later_in_the_sentence():
    r = run_case(FakeEditor(generalizes=True, answer=" speaker of OMEGA-99"), CASE)
    assert not r.edit_success                 # exact prompt must answer immediately
    assert r.paraphrase_generalization == 1.0  # paraphrase only needs a new mention


def test_paraphrase_does_not_count_if_base_already_said_it():
    case = EditCase(id="pre", prompt="P is", target=" kitten", paraphrases=["A baby cat is called a"])
    r = run_case(FakeEditor(generalizes=True), case)
    assert r.paraphrase_generalization == 0.0


def test_bleeding_editor_hurts_easy_locality_only():
    r = run_case(FakeEditor(bleeds=True), CASE)
    assert r.locality == 0.0 and r.locality_hard == 1.0


def test_hard_negative_bleed_is_reported_separately():
    r = run_case(FakeEditor(bleeds_hard=True), CASE)
    assert r.locality == 1.0 and r.locality_hard == 0.0


def test_leaky_revocation_is_caught():
    r = run_case(FakeEditor(leaks=True), CASE)
    assert not r.revocation_exact
    assert r.target_leak_after_revoke == pytest.approx(2 / 3)  # 2 of 3 target probes leak


def test_inexact_but_non_leaking_revocation():
    """Output changed after revoke but the target is gone: not exact, no leak."""
    r = run_case(FakeEditor(sticky=True), CASE)
    assert not r.revocation_exact
    assert r.target_leak_after_revoke == 0.0


def test_missing_probe_types_give_nan_not_crash():
    case = EditCase(id="bare", prompt="X is", target=" Y")
    r = run_case(FakeEditor(), case)
    assert math.isnan(r.paraphrase_generalization) and math.isnan(r.locality_hard)
    s = summarize([r])
    assert math.isnan(s["paraphrase_generalization"])


def test_duplicate_probes_are_deduplicated():
    case = EditCase(id="dup", prompt="X is", target=" Y", unrelated=["Water boils at"],
                    hard_negatives=["Water boils at"])
    r = run_case(FakeEditor(), case)
    assert len(r.outputs) == 2


def test_base_cache_skips_repeat_base_generations():
    calls = []

    class Counting(FakeEditor):
        def generate(self, prompt, max_new_tokens=8):
            calls.append(prompt)
            return super().generate(prompt, max_new_tokens)

    cache = {}
    r1 = run_suite(Counting(), [CASE], base_cache=cache)
    first = len(calls)
    r2 = run_suite(Counting(), [CASE], base_cache=cache)
    n_probes = len(r1[0].outputs)
    assert len(calls) - first == first - n_probes   # second run skips the base pass
    strip = lambda r: {k: v for k, v in r.to_dict().items() if not k.endswith("_ms")}
    assert strip(r1[0]) == strip(r2[0])


def test_base_cache_is_keyed_by_generation_length():
    cache = {}
    run_suite(FakeEditor(), [CASE], max_new_tokens=8, base_cache=cache)
    run_suite(FakeEditor(), [CASE], max_new_tokens=4, base_cache=cache)
    assert {k[1] for k in cache} == {4, 8}


def test_summary_and_save(tmp_path):
    results = run_suite(FakeEditor(), [CASE, CASE])
    s = summarize(results)
    assert s["n_cases"] == 2 and s["edit_success"] == 1.0 and s["locality_hard"] == 1.0
    jp, mp = save_run(results, s, "fake", {"x": 1}, out_dir=tmp_path, tag="t")
    data = json.loads(jp.read_text())
    assert data["summary"]["edit_success"] == 1.0
    assert len(data["cases"]) == 2
    assert jp.name.endswith("_fake_t.json")
    assert "| locality_hard |" in mp.read_text()


def test_bundled_fictional_cases_load():
    cases = load_cases("cases/fictional_v0.jsonl")
    assert len(cases) == 5
    for c in cases:
        assert c.paraphrases and c.unrelated and c.hard_negatives
        assert c.subject and c.subject in c.prompt
    assert len({c.id for c in cases}) == 5
