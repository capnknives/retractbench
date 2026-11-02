"""Precomputed (replayed) rank-one edits on the tiny random Llama. Mechanics only."""
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")

from retractbench import run_case  # noqa: E402
from retractbench.editors.precomputed import PrecomputedRomeEditor, load_easyedit_updates  # noqa: E402
from retractbench.editors.rome import drop_top_singular  # noqa: E402
from test_grace_tiny import CASE  # noqa: E402
from test_rome_tiny import editor, make_tiny  # noqa: E402


@pytest.fixture()
def tiny_with_update():
    """A real trained update from RomeEditor on the tiny model, to replay."""
    model, tok = make_tiny()
    ed = editor(model, tok, revoke_mode="restore")
    try:
        h = ed.apply(CASE)
        dW = h["dW"].clone()
    finally:
        ed.close()
    return model, tok, dW


def test_replay_matches_original_edit_and_restore_is_exact(tiny_with_update):
    model, tok, dW = tiny_with_update
    ed = PrecomputedRomeEditor(model, tok, {CASE.id: dW}, layer=1, revoke_mode="restore")
    try:
        W0 = ed.W.detach().clone()
        r = run_case(ed, CASE, max_new_tokens=3)
        assert r.edit_success, r.outputs[CASE.prompt]
        assert r.revocation_exact
        assert torch.equal(ed.W, W0)
        assert ed.revoke_log[-1]["edit_fro"] == pytest.approx(dW.norm().item(), rel=1e-5)
    finally:
        ed.close()


def test_subtract_and_svd_modes(tiny_with_update):
    model, tok, dW = tiny_with_update
    for mode, name in (("subtract", "easyedit-rome-subtract"), ("svd", "easyedit-rome-svd1")):
        ed = PrecomputedRomeEditor(model, tok, {CASE.id: dW}, layer=1, revoke_mode=mode, svd_q=1)
        try:
            assert ed.name == name
            W0 = ed.W.detach().clone()
            h = ed.apply(CASE)
            ed.revoke(h)
            if mode == "svd":
                expected = drop_top_singular(W0 + dW, 1)
                assert torch.allclose(ed.W, expected, atol=1e-5)
            else:
                assert ed.revoke_log[-1]["residual_fro"] < 1e-5 * dW.norm().item()
        finally:
            ed.close()


def test_rejects_inverse_wrong_shape_and_unknown_case(tiny_with_update):
    model, tok, dW = tiny_with_update
    with pytest.raises(ValueError):
        PrecomputedRomeEditor(model, tok, {CASE.id: dW}, layer=1, revoke_mode="inverse")
    with pytest.raises(ValueError):
        PrecomputedRomeEditor(model, tok, {CASE.id: dW.T}, layer=1)
    ed = PrecomputedRomeEditor(model, tok, {"other": dW}, layer=1)
    try:
        with pytest.raises(KeyError):
            ed.apply(CASE)
    finally:
        ed.close()


def test_load_easyedit_updates_rebuilds_outer_product(tmp_path):
    u, v = torch.randn(5), torch.randn(3)
    blob = {"meta": {"weight_shape": [3, 5]},
            "cases": {"a": {"left": u, "right": v, "transpose": True, "rewrite_acc_post": 1.0},
                      "b": {"left": v, "right": u, "transpose": False, "rewrite_acc_post": 0.5}}}
    p = tmp_path / "x.pt"
    torch.save(blob, p)
    updates, meta, info = load_easyedit_updates(str(p))
    assert torch.allclose(updates["a"], torch.outer(u, v).T)
    assert torch.allclose(updates["b"], torch.outer(v, u))
    assert updates["a"].shape == (3, 5) and updates["b"].shape == (3, 5)
    assert info["b"]["rewrite_acc_post"] == 0.5 and "left" not in info["a"]
