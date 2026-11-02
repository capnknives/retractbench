"""margin_scores (CounterFact ES/PS/NS) with fake editors whose log-probs we choose."""
import math

from retractbench.harness import run_case, run_suite, summarize
from retractbench.types import EditCase

CASE = EditCase(id="c1", prompt="X is located in", target=" Paris", target_true=" Rome",
                paraphrases=["X lies in", "X can be found in"],
                unrelated=["2 + 2 ="], hard_negatives=["Y is located in", "Z is located in"])


class FakeLP:
    """Prefers the true object, except on the edited prompt and paraphrases while edited.
    bleed=True: the edit also flips the hard negatives. trace=True: revoke leaves the edit in."""
    name = "fake-lp"

    def __init__(self, bleed=False, trace=False):
        self.edited, self.bleed, self.trace = False, bleed, trace

    def generate(self, prompt, max_new_tokens=8):
        return " same"

    def apply(self, case):
        self.edited = True

    def revoke(self, handle):
        self.edited = self.trace

    def config(self):
        return {}

    def logprob(self, prompt, continuation):
        is_target = continuation == CASE.target
        flipped = self.edited and (prompt in [CASE.prompt, *CASE.paraphrases] or self.bleed)
        return (-1.0 if is_target else -5.0) if flipped else (-5.0 if is_target else -1.0)


def test_clean_edit_and_undo():
    m = run_case(FakeLP(), CASE).margins
    assert m["base"] == {"es": 0.0, "ps": 0.0, "ns": 1.0}
    assert m["after_write"] == {"es": 1.0, "ps": 1.0, "ns": 1.0}
    assert m["after_revoke"] == m["base"]


def test_bleed_shows_in_ns():
    m = run_case(FakeLP(bleed=True), CASE).margins
    assert m["after_write"]["ns"] == 0.0
    assert m["after_revoke"]["ns"] == 1.0


def test_trace_after_undo_shows():
    m = run_case(FakeLP(trace=True), CASE).margins
    assert m["after_revoke"] == {"es": 1.0, "ps": 1.0, "ns": 1.0}


def test_no_target_true_gives_nan():
    case = EditCase(id="f1", prompt="X is located in", target=" Paris", paraphrases=["X lies in"])
    m = run_case(FakeLP(), case).margins
    assert all(math.isnan(v) for v in m["base"].values())


def test_editor_without_logprob_has_no_margins():
    class NoLP(FakeLP):
        logprob = None
    r = run_case(NoLP(), CASE)
    assert r.margins == {}
    assert not any(k.startswith("es_") for k in summarize([r]))


def test_summary_keys():
    # A clean fake: a trace=True fake has no reset(), so its leftover edit would (correctly)
    # show up in the second case's base scores.
    s = summarize(run_suite(FakeLP(), [CASE, CASE]))
    assert s["es_base"] == 0.0 and s["es_after_write"] == 1.0 and s["es_after_revoke"] == 0.0
    assert s["ns_base"] == 1.0
