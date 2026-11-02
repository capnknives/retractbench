## 2026-11-02 (09:30): leak check for real-world facts, a second count (not a replacement)

**Metric change** (harness.py, per CLAUDE.md): `target_leak_after_revoke` is unchanged. Added `target_leak_excl_true`: same, but a probe does not count as leaking if its after-revoke answer also mentions the true object. Both use the new `harness.leak_flags`. Without a `target_true` (fictional cases) the two are identical. New tests in `tests/test_harness.py` (target inside a true answer, target alone, target already in base, no target_true); 71 tests pass.

**Re-scored the cf100 layer-4 runs from stored outputs** (`scripts/rescore_leaks.py`, `results/20261102T085843_rescore_leaks.json`; original run files untouched). The recomputed plain counts match the stored ones exactly (subtract 0.000, inverse 0.020, inverse-true 0.020), so the refactor did not change the old metric.

| run | leak (plain) | leak excl. true | leaky cases: plain / strict |
| --- | --- | --- | --- |
| subtract | 0.000 | 0.000 | 0 / 0 |
| inverse (base tokens) | 0.020 | 0.017 | 5 / 4 |
| inverse (true object) | 0.020 | 0.010 | 5 / 2 |

**The stricter count is not simply better.** Of the three inverse-true cases it drops: cf10819 "Fiat Chrysler Automobiles" is a correct answer (right to drop); cf18105 "chemistry, not mathematics" is a genuine trace of the removed edit (wrong to drop); cf4267 "French, English, and Latin" is ambiguous. So one false positive fixed, one false negative introduced. Neither string rule decides this correctly.

**Decision for the write-up:** report the plain count, list every leaking case with its text, and hand-label each (true answer / trace / ambiguous). At this sample size (5 cases per run) a labelled list is more honest than either automatic number. A model-based or answer-slot check is possible later but not needed now.

