"""ROME-style editor on a tiny random Llama (CPU). Mechanics, not quality.

As with GRACE, subject-position edits can't be trained on a 32-dim random
model, so trained-edit tests use key_position="last".
"""
import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")

from retractbench import EditCase, run_case  # noqa: E402
from retractbench.editors.rome import RomeEditor, _F32Linear  # noqa: E402
from test_grace_tiny import CASE, WordTokenizer  # noqa: E402


def make_tiny(dtype=torch.float32):
    torch.manual_seed(0)
    cfg = transformers.LlamaConfig(
        vocab_size=64, hidden_size=32, intermediate_size=64, num_hidden_layers=4,
        num_attention_heads=4, num_key_value_heads=4, max_position_embeddings=64,
        pad_token_id=0, bos_token_id=1, eos_token_id=63,
    )
    model = transformers.LlamaForCausalLM(cfg).to(dtype).eval()
    texts = [CASE.prompt, CASE.target, *CASE.paraphrases, *CASE.unrelated, *CASE.hard_negatives]
    return model, WordTokenizer(texts, cfg.vocab_size)


@pytest.fixture()
def tiny():
    return make_tiny()


def editor(model, tok, **kw):
    kw = {"layer": 1, "key_position": "last", "steps": 300, "lr": 0.5, "tol": 0.01, "clamp_factor": 100.0, **kw}
    return RomeEditor(model, tok, **kw)


def test_restore_is_exact_and_bitwise(tiny):
    model, tok = tiny
    ed = editor(model, tok, revoke_mode="restore")
    try:
        W0 = ed.W.detach().clone()
        r = run_case(ed, CASE, max_new_tokens=3)
        assert r.edit_success, (ed.last_fit, r.outputs[CASE.prompt])
        assert r.revocation_exact and r.target_leak_after_revoke == 0.0
        assert torch.equal(ed.W, W0)
        assert ed.revoke_log[-1]["residual_fro"] == 0.0
    finally:
        ed.close()


def test_subtract_leaves_only_rounding_residue(tiny):
    model, tok = tiny
    ed = editor(model, tok, revoke_mode="subtract")
    try:
        r = run_case(ed, CASE, max_new_tokens=3)
        assert r.edit_success
        log = ed.revoke_log[-1]
        assert log["residual_fro"] < 1e-5 * max(log["edit_fro"], 1.0)
        assert r.revocation_exact, r.outputs
    finally:
        ed.close()


def test_inverse_edit_counters_but_leaves_weights_changed(tiny):
    model, tok = tiny
    ed = editor(model, tok, revoke_mode="inverse", inverse_tokens=2)
    try:
        r = run_case(ed, CASE, max_new_tokens=3)
        assert r.edit_success
        log = ed.revoke_log[-1]
        assert "revert_target" in log
        assert log["residual_fro"] > 0.0    # the original edit is still in the weights
    finally:
        ed.close()


def test_close_restores_original_module(tiny):
    model, tok = tiny
    orig = model.model.layers[1].mlp.down_proj
    ed = editor(model, tok)
    assert isinstance(model.model.layers[1].mlp.down_proj, _F32Linear)
    ed.close()
    assert model.model.layers[1].mlp.down_proj is orig


def test_float32_wrapper_does_not_change_outputs_of_fp32_model(tiny):
    model, tok = tiny
    ids = torch.tensor([tok.encode(CASE.prompt)])
    with torch.no_grad():
        before = model(ids).logits
    ed = editor(model, tok)
    try:
        with torch.no_grad():
            after = model(ids).logits
        assert torch.allclose(before, after, atol=1e-6)
    finally:
        ed.close()


def test_native_bf16_rounds_away_part_of_the_edit():
    model, tok = make_tiny(torch.bfloat16)
    ed = editor(model, tok, weight_dtype="native", revoke_mode="subtract", steps=50)
    try:
        ed.apply(CASE)
        assert ed.last_fit["applied_vs_intended"] > 0.0   # bf16 can't hold the update exactly
    finally:
        ed.close()


def test_calibration_covariance_runs(tiny):
    model, tok = tiny
    ed = editor(model, tok, covariance="calibration", steps=5)
    try:
        h = ed.apply(CASE)
        ed.revoke(h)
        assert ed.calibration_tokens > 50
        assert ed.name == "rome-last-restore-cov"
    finally:
        ed.close()


def test_subject_mode_requires_subject(tiny):
    model, tok = tiny
    ed = RomeEditor(model, tok, layer=1)
    try:
        with pytest.raises(ValueError):
            ed.apply(EditCase(id="x", prompt=CASE.prompt, target=" OMEGA-99"))
    finally:
        ed.close()


def test_isolation_resets_residue_between_cases(tiny):
    from retractbench import run_suite
    model, tok = tiny
    ed = editor(model, tok, revoke_mode="inverse", inverse_tokens=2, steps=50)
    try:
        W0 = ed.W.detach().clone()
        run_suite(ed, [CASE, CASE], max_new_tokens=3, isolate=True)
        assert torch.equal(ed.W, W0)
        run_suite(ed, [CASE], max_new_tokens=3, isolate=False)
        assert not torch.equal(ed.W, W0)          # residue kept on purpose
        ed.reset()
        assert torch.equal(ed.W, W0)
    finally:
        ed.close()


def test_inverse_toward_true_object(tiny):
    import dataclasses
    model, tok = tiny
    case = dataclasses.replace(CASE, target_true=" The")   # a word in the tiny vocab
    ed = editor(model, tok, revoke_mode="inverse", inverse_target="true", steps=50)
    try:
        assert ed.name == "rome-last-inverse-true"
        h = ed.apply(case)
        assert h["revert_target"] == " The"
        ed.revoke(h)
        assert ed.revoke_log[-1]["revert_target"] == " The"
        with pytest.raises(ValueError):
            ed.apply(CASE)                                   # no target_true
    finally:
        ed.close()
