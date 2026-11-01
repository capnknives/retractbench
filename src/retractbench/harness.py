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


def run_case(editor: Editor, case: EditCase, max_new_tokens: int = 8,
             base_cache: dict | None = None) -> CaseResult:
    """`base_cache` ((prompt, max_new_tokens) -> base output) lets several runs on
    the same model share the unedited answers. Only valid when the editor holds
    no edits at the start of the case, which run_suite guarantees (each case is
    revoked before the next). Don't share a cache across different models."""
    # dict.fromkeys de-duplicates while keeping order
    probes = list(dict.fromkeys([case.prompt, *case.paraphrases, *case.unrelated, *case.hard_negatives]))
    gen = lambda p: editor.generate(p, max_new_tokens=max_new_tokens)

    base = {}
    for p in probes:
        key = (p, max_new_tokens)
        if base_cache is not None and key in base_cache:
            base[p] = base_cache[key]
        else:
            base[p] = gen(p)
            if base_cache is not None:
                base_cache[key] = base[p]

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
              progress: bool = False, base_cache: dict | None = None,
              isolate: bool = True) -> list[CaseResult]:
    """Run cases one after another: write, probe, revoke, probe.

    isolate=True (default): if the editor has a `reset()` method, call it after
    every case, so each case starts from the pristine model even when an undo
    method leaves residue. Without this, residue accumulates across cases
    (found 2026-11-01: inverse-edit runs drifted the model case after case).
    isolate=False measures that accumulated drift on purpose; don't combine it
    with a shared base_cache, since the cached base outputs come from the
    pristine model."""
    if not isolate and base_cache is not None:
        raise ValueError("isolate=False with a shared base_cache compares against the wrong base")
    cases = list(cases)
    out = []
    t0 = time.perf_counter()
    for i, c in enumerate(cases, 1):
        t_case = time.perf_counter()
        out.append(run_case(editor, c, max_new_tokens, base_cache=base_cache))
        if isolate and hasattr(editor, "reset"):
            editor.reset()
        if progress:
            dt = time.perf_counter() - t_case
            line = f"  case {i}/{len(cases)} {c.id} ({dt:.0f}s)"
            if i % 10 == 0 or i == len(cases):
                avg = (time.perf_counter() - t0) / i
                line += f"  avg {avg:.0f}s/case, ~{avg * (len(cases) - i) / 60:.0f} min left"
            print(line, flush=True)
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
