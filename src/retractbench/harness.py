"""The revocation protocol: base -> apply -> probe -> revoke -> probe.

Pure Python. Works with any object that satisfies `retractbench.types.Editor`.

Target matching (changed 2026-11-01, see LOG.md):
- `answers_with_target`: the output *starts* with the target, followed by a
  word boundary. Used for edit success on the exact prompt, which is written
  so the answer comes next. " OMEGA-999" does not count for target " OMEGA-99".
- `mentions_target`: the target appears anywhere with word boundaries on both
  sides. Used for leak detection, where any mention counts.
- Paraphrase generalization counts a paraphrase when the target is *newly*
  mentioned: present after the edit, absent from the base model's answer.
  Paraphrases are often phrased so the answer comes later in the sentence
  (CounterFact: "Danielle Darrieux, a native" -> " speaker of English").
- `edit_success_loose` keeps the original plain-substring check for comparison.
"""
from __future__ import annotations

import re
import time
from typing import Iterable

from .types import CaseResult, EditCase, Editor


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def answers_with_target(output: str, target: str) -> bool:
    o, t = _norm(output), _norm(target)
    if not t or not o.startswith(t):
        return False
    return len(o) == len(t) or not o[len(t)].isalnum()


def mentions_target(output: str, target: str) -> bool:
    t = _norm(target)
    if not t:
        return False
    return re.search(rf"(?<!\w){re.escape(t)}(?!\w)", _norm(output)) is not None


def contains_substring(output: str, target: str) -> bool:
    t = target.strip().lower()
    return bool(t) and t in output.lower()


def _frac(xs: list[bool]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def run_case(editor: Editor, case: EditCase, max_new_tokens: int = 8) -> CaseResult:
    # dict.fromkeys de-duplicates while keeping order
    probes = list(dict.fromkeys([case.prompt, *case.paraphrases, *case.unrelated, *case.hard_negatives]))
    gen = lambda p: editor.generate(p, max_new_tokens=max_new_tokens)

    base = {p: gen(p) for p in probes}

    t0 = time.perf_counter()
    handle = editor.apply(case)
    apply_ms = (time.perf_counter() - t0) * 1000
    after_write = {p: gen(p) for p in probes}

    t0 = time.perf_counter()
    editor.revoke(handle)
    revoke_ms = (time.perf_counter() - t0) * 1000
    after_revoke = {p: gen(p) for p in probes}

    target_probes = [case.prompt, *case.paraphrases]
    # A leak counts only if the target appears after revocation where it did
    # not appear in the base model's answer to the same probe.
    leaks = [
        mentions_target(after_revoke[p], case.target) and not mentions_target(base[p], case.target)
        for p in target_probes
    ]

    return CaseResult(
        case_id=case.id,
        edit_success=answers_with_target(after_write[case.prompt], case.target),
        edit_success_loose=contains_substring(after_write[case.prompt], case.target),
        paraphrase_generalization=_frac([
            mentions_target(after_write[p], case.target) and not mentions_target(base[p], case.target)
            for p in case.paraphrases
        ]),
        locality=_frac([after_write[p] == base[p] for p in case.unrelated]),
        locality_hard=_frac([after_write[p] == base[p] for p in case.hard_negatives]),
        revocation_exact=all(after_revoke[p] == base[p] for p in probes),
        target_leak_after_revoke=_frac(leaks),
        apply_ms=apply_ms,
        revoke_ms=revoke_ms,
        outputs={
            p: {"base": base[p], "after_write": after_write[p], "after_revoke": after_revoke[p]}
            for p in probes
        },
    )


def run_suite(editor: Editor, cases: Iterable[EditCase], max_new_tokens: int = 8,
              progress: bool = False) -> list[CaseResult]:
    """Each case is independent: written, probed, revoked, before the next one.
    (Sequential / lifelong editing is a later mode.)"""
    cases = list(cases)
    out = []
    for i, c in enumerate(cases, 1):
        out.append(run_case(editor, c, max_new_tokens))
        if progress:
            print(f"  case {i}/{len(cases)} {c.id}", flush=True)
    return out


def summarize(results: list[CaseResult]) -> dict:
    def mean(xs):
        xs = [x for x in xs if x == x]  # drop NaN
        return sum(xs) / len(xs) if xs else float("nan")

    return {
        "n_cases": len(results),
        "edit_success": mean([float(r.edit_success) for r in results]),
        "edit_success_loose": mean([float(r.edit_success_loose) for r in results]),
        "paraphrase_generalization": mean([r.paraphrase_generalization for r in results]),
        "locality": mean([r.locality for r in results]),
        "locality_hard": mean([r.locality_hard for r in results]),
        "revocation_exact": mean([float(r.revocation_exact) for r in results]),
        "target_leak_after_revoke": mean([r.target_leak_after_revoke for r in results]),
        "apply_ms_mean": mean([r.apply_ms for r in results]),
        "revoke_ms_mean": mean([r.revoke_ms for r in results]),
    }
