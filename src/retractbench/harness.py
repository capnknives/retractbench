"""The revocation protocol: base -> apply -> probe -> revoke -> probe.

Pure Python. Works with any object that satisfies `retractbench.types.Editor`.
"""
from __future__ import annotations

import time
from typing import Iterable

from .types import CaseResult, EditCase, Editor


def _contains_target(text: str, target: str) -> bool:
    t = target.strip().lower()
    return bool(t) and t in text.lower()


def _frac(xs: list[bool]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def run_case(editor: Editor, case: EditCase, max_new_tokens: int = 8) -> CaseResult:
    probes = [case.prompt, *case.paraphrases, *case.unrelated]
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
        _contains_target(after_revoke[p], case.target)
        and not _contains_target(base[p], case.target)
        for p in target_probes
    ]

    return CaseResult(
        case_id=case.id,
        edit_success=_contains_target(after_write[case.prompt], case.target),
        paraphrase_generalization=_frac(
            [_contains_target(after_write[p], case.target) for p in case.paraphrases]
        ),
        locality=_frac([after_write[p] == base[p] for p in case.unrelated]),
        revocation_exact=all(after_revoke[p] == base[p] for p in probes),
        target_leak_after_revoke=_frac(leaks),
        apply_ms=apply_ms,
        revoke_ms=revoke_ms,
        outputs={
            p: {"base": base[p], "after_write": after_write[p], "after_revoke": after_revoke[p]}
            for p in probes
        },
    )


def run_suite(editor: Editor, cases: Iterable[EditCase], max_new_tokens: int = 8) -> list[CaseResult]:
    """Each case is independent: written, probed, revoked, before the next one.
    (Sequential / lifelong editing is a later mode.)"""
    return [run_case(editor, c, max_new_tokens) for c in cases]


def summarize(results: list[CaseResult]) -> dict:
    def mean(xs):
        xs = [x for x in xs if x == x]  # drop NaN
        return sum(xs) / len(xs) if xs else float("nan")

    return {
        "n_cases": len(results),
        "edit_success": mean([float(r.edit_success) for r in results]),
        "paraphrase_generalization": mean([r.paraphrase_generalization for r in results]),
        "locality": mean([r.locality for r in results]),
        "revocation_exact": mean([float(r.revocation_exact) for r in results]),
        "target_leak_after_revoke": mean([r.target_leak_after_revoke for r in results]),
        "apply_ms_mean": mean([r.apply_ms for r in results]),
        "revoke_ms_mean": mean([r.revoke_ms for r in results]),
    }
