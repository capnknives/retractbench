"""The case builder's two selection modes, on a tiny synthetic CounterFact-shaped list (no download, no torch)."""
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("make_counterfact_cases", ROOT / "scripts" / "make_counterfact_cases.py")
mcc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcc)


def record(case_id: int, rel: str) -> dict:
    return {
        "case_id": case_id,
        "requested_rewrite": {
            "prompt": "{} is in the city of", "subject": f"Subject{case_id}", "relation_id": rel,
            "target_new": {"str": f"New{case_id}"}, "target_true": {"str": f"Old{case_id}"},
        },
        "paraphrase_prompts": [f"p{case_id}a", f"p{case_id}b"],
        "neighborhood_prompts": [f"n{case_id}_{i}" for i in range(6)],
    }


def synthetic() -> list[dict]:
    """Relations A (5 records), B (4), C (2, too small for min size 3), D (3); interleaved in file order."""
    order = ["A", "B", "A", "C", "D", "B", "A", "D", "B", "A", "C", "D", "B", "A"]
    return [record(100 + i, rel) for i, rel in enumerate(order)]


def run_main(tmp_path, monkeypatch, *argv) -> list[str]:
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "cases").mkdir(exist_ok=True)
    data = tmp_path / "data" / "cf.json"
    data.write_text(json.dumps(synthetic()), encoding="utf-8")
    monkeypatch.setattr(mcc, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["make_counterfact_cases.py", "--data", str(data), "--name", "out", *argv])
    mcc.main()
    return (tmp_path / "cases" / "out.jsonl").read_text(encoding="utf-8").splitlines()


def cases_of(lines: list[str]) -> list[dict]:
    return [json.loads(x) for x in lines if x.strip() and not x.startswith("#")]


def test_small_relations_dropped():
    picked = mcc.pick_per_relation(synthetic(), 2, 3, set())
    assert {r["requested_rewrite"]["relation_id"] for r in picked} == {"A", "B", "D"}  # C has 2 records


def test_first_k_per_relation_in_dataset_order():
    picked = mcc.pick_per_relation(synthetic(), 2, 3, set())
    by_rel = {}
    for r in picked:
        by_rel.setdefault(r["requested_rewrite"]["relation_id"], []).append(r["case_id"])
    assert by_rel == {"A": [100, 102], "B": [101, 105], "D": [104, 107]}
    # output order: relations by first appearance in the file
    assert [r["requested_rewrite"]["relation_id"] for r in picked] == ["A"] * 2 + ["B"] * 2 + ["D"] * 2


def test_relation_with_fewer_than_k_records_gives_what_it_has():
    picked = mcc.pick_per_relation(synthetic(), 4, 3, set())
    assert sum(r["requested_rewrite"]["relation_id"] == "D" for r in picked) == 3  # D has 3 records in all


def test_excluded_ids_skipped_and_size_counted_before_exclusion():
    picked = mcc.pick_per_relation(synthetic(), 2, 3, {"cf100", "cf104"})
    ids = [r["case_id"] for r in picked]
    assert 100 not in ids and 104 not in ids
    assert ids[:2] == [102, 106]  # A: the next records in order
    # D has 3 records, so it still counts as large at min size 3 although one is excluded
    assert ids[-2:] == [107, 111]
    # a relation just under the threshold stays out: D (3) at min size 4
    assert {r["requested_rewrite"]["relation_id"] for r in mcc.pick_per_relation(synthetic(), 2, 4, set())} == {"A", "B"}


def test_new_mode_deterministic_and_header_records_command(tmp_path, monkeypatch):
    a = run_main(tmp_path, monkeypatch, "--per-relation", "2", "--min-relation-size", "3", "--seed", "7")
    b = run_main(tmp_path, monkeypatch, "--per-relation", "2", "--min-relation-size", "3", "--seed", "7")
    assert a == b
    assert a[0].startswith("# Sampled from CounterFact")
    assert "--per-relation 2 --min-relation-size 3 --seed 7" in a[0] and "--name out" in a[0]
    cases = cases_of(a)
    assert len(cases) == 6
    for c in cases:
        assert len(c["unrelated"]) == 3
        assert all(c["subject"] not in u for u in c["unrelated"])  # drawn from other relations only
        assert len(c["hard_negatives"]) == 5


def test_new_mode_default_min_size_is_200(tmp_path, monkeypatch):
    lines = run_main(tmp_path, monkeypatch, "--per-relation", "2")
    assert cases_of(lines) == []  # the synthetic relations are all far below 200
    assert "--min-relation-size 200" in lines[0]


def legacy_reference(records, n, seed, excluded, n_hard=5, n_easy=3):
    """The random mode exactly as it was before --per-relation existed."""
    records = [r for r in records if f"cf{r['case_id']}" not in excluded]
    rng = random.Random(seed)
    picked = rng.sample(records, n)
    out = []
    for r in picked:
        rw = r["requested_rewrite"]
        others = [o for o in picked if o["requested_rewrite"]["relation_id"] != rw["relation_id"]]
        easy = [o["requested_rewrite"]["prompt"].format(o["requested_rewrite"]["subject"]) for o in rng.sample(others, n_easy)]
        out.append({"id": f"cf{r['case_id']}", "unrelated": easy, "hard_negatives": r["neighborhood_prompts"][:n_hard]})
    return out


def test_legacy_random_mode_unchanged(tmp_path, monkeypatch):
    lines = run_main(tmp_path, monkeypatch, "--n", "8", "--seed", "3")
    assert lines[0].endswith("with `python scripts/make_counterfact_cases.py --n 8 --seed 3 --name out`.")
    got = [{k: c[k] for k in ("id", "unrelated", "hard_negatives")} for c in cases_of(lines)]
    assert got == legacy_reference(synthetic(), 8, 3, set())


def test_min_relation_size_alone_is_an_error(tmp_path, monkeypatch):
    with pytest.raises(SystemExit):
        run_main(tmp_path, monkeypatch, "--min-relation-size", "3")


@pytest.mark.skipif(not (ROOT / "data" / "counterfact.json").exists(), reason="data/counterfact.json not downloaded")
def test_committed_case_file_regenerates_identically(tmp_path, monkeypatch):
    for name, n, seed in (("counterfact_100_seed0", 100, 0),):
        monkeypatch.setattr(mcc, "ROOT", tmp_path)
        (tmp_path / "cases").mkdir(exist_ok=True)
        monkeypatch.setattr(sys, "argv", ["x", "--n", str(n), "--seed", str(seed), "--data", str(ROOT / "data" / "counterfact.json")])
        mcc.main()
        assert (tmp_path / "cases" / f"{name}.jsonl").read_bytes() == (ROOT / "cases" / f"{name}.jsonl").read_bytes()
