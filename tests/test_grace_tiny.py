"""GRACE editor on a tiny randomly initialized Llama. CPU only, no downloads.

This checks mechanics (hooks, write, revoke, key options), not quality: a
random model says nothing meaningful. Real numbers come from `retractbench run`.
"""
import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")

from retractbench import EditCase, run_case  # noqa: E402
from retractbench.editors.grace import Codebook, GraceEditor, subject_last_index  # noqa: E402
from retractbench.separability import measure  # noqa: E402


class WordTokenizer:
    """Whitespace tokenizer over a fixed vocabulary. 0 = pad, 1 = bos, 2 = unknown word."""

    def __init__(self, texts, vocab_size):
        words = sorted({w for t in texts for w in t.split()})
        assert len(words) + 3 <= vocab_size, "vocab too small for test strings"
        self.w2i = {w: i + 3 for i, w in enumerate(words)}
        self.i2w = {i: w for w, i in self.w2i.items()}

    def encode(self, text, add_special_tokens=True):
        ids = [self.w2i.get(w, 2) for w in text.split()]
        return ([1] + ids) if add_special_tokens else ids

    def decode(self, ids, skip_special_tokens=True):
        return " ".join(self.i2w.get(i, f"<{i}>") for i in ids if not (skip_special_tokens and i < 3))


CASE = EditCase(
    id="titan",
    subject="Project Titan",
    prompt="The secret code of Project Titan is",
    target=" OMEGA-99",
    paraphrases=["Project Titan secret code is"],
    unrelated=["The capital of France is", "Water boils at"],
    hard_negatives=["The secret code of Project Apollo is"],
)


@pytest.fixture(scope="module")
def tiny():
    torch.manual_seed(0)
    cfg = transformers.LlamaConfig(
        vocab_size=64, hidden_size=32, intermediate_size=64, num_hidden_layers=4,
        num_attention_heads=4, num_key_value_heads=4, max_position_embeddings=64,
        pad_token_id=0, bos_token_id=1, eos_token_id=63,
    )
    model = transformers.LlamaForCausalLM(cfg).eval()
    texts = [CASE.prompt, CASE.target, *CASE.paraphrases, *CASE.unrelated, *CASE.hard_negatives]
    return model, WordTokenizer(texts, cfg.vocab_size)


def test_codebook_add_lookup_delete():
    cb = Codebook(eps=0.1)
    k = torch.tensor([1.0, 0.0, 0.0])
    eid = cb.add(k, torch.tensor([0.0, 5.0, 0.0]), "x")
    assert cb.lookup(torch.tensor([1.0, 0.01, 0.0])) is not None  # near the key
    assert cb.lookup(torch.tensor([0.0, 1.0, 0.0])) is None        # orthogonal
    assert cb.delete(eid) and len(cb) == 0
    assert cb.lookup(k) is None


def test_subject_last_index(tiny):
    _, tok = tiny
    # tokens: <bos> The secret code of Project Titan is  -> "Titan" is index 6
    assert subject_last_index(tok, CASE.prompt, "Project Titan") == 6
    with pytest.raises(ValueError):
        subject_last_index(tok, CASE.prompt, "Hermes")


def test_weights_are_frozen(tiny):
    model, tok = tiny
    ed = GraceEditor(model, tok, steps=1)
    try:
        assert not any(p.requires_grad for p in model.parameters())
    finally:
        ed.close()


@pytest.mark.parametrize("key_space", ["raw", "standardized"])
def test_write_then_revoke_restores_base(tiny, key_space):
    model, tok = tiny
    ed = GraceEditor(model, tok, layer=2, eps=0.05, steps=150, lr=0.1, tol=0.01,
                     key_position="last", key_space=key_space)
    try:
        r = run_case(ed, CASE, max_new_tokens=3)
        assert r.edit_success, (ed.last_fit, r.outputs[CASE.prompt])
        assert r.revocation_exact, r.outputs
        assert r.target_leak_after_revoke == 0.0
        assert len(ed.codebook) == 0
        assert ed.name == f"grace-last-{key_space}"
    finally:
        ed.close()


@pytest.mark.parametrize("key_space", ["raw", "standardized"])
def test_subject_mode_replaces_only_the_subject_position(tiny, key_space):
    """Subject-keyed edits can't be *trained* on this tiny model: a 32-dim random
    network can't carry a change at the subject token through to the answer
    (loss plateaus near chance at every layer and lr; see LOG.md). So this test
    checks the mechanism directly: plant an entry, confirm the hook rewrites
    the subject position and nothing else, and that revoking restores it."""
    model, tok = tiny
    ed = GraceEditor(model, tok, layer=2, eps=1e-3, key_position="subject", key_space=key_space)
    seen = {}
    cap = ed.layers[2].register_forward_hook(lambda m, i, o: seen.__setitem__("H", o[0].clone() if isinstance(o, tuple) else o.clone()))
    try:
        before = ed._layer_states(CASE.prompt)
        value = torch.full_like(before[6], 7.0)
        eid = ed.codebook.add(ed.case_key(CASE), value, "planted")
        with torch.no_grad():
            model(ed._ids(CASE.prompt, True))
        H = seen["H"][0].float()
        assert torch.allclose(H[6], value, atol=1e-5)
        others = [i for i in range(H.shape[0]) if i != 6]
        assert torch.allclose(H[others], before[others], atol=1e-5)
        ed.revoke(eid)
        with torch.no_grad():
            model(ed._ids(CASE.prompt, True))
        assert torch.allclose(seen["H"][0].float(), before, atol=1e-5)
    finally:
        cap.remove()
        ed.close()


def test_subject_mode_never_matches_position_zero(tiny):
    """Position 0 is the attention sink; a key there would fire on every prompt."""
    model, tok = tiny
    ed = GraceEditor(model, tok, layer=2, eps=1e-3, key_position="subject")
    seen = {}
    cap = ed.layers[2].register_forward_hook(lambda m, i, o: seen.__setitem__("H", (o[0] if isinstance(o, tuple) else o).clone()))
    try:
        before = ed._layer_states(CASE.prompt)
        ed.codebook.add(ed.to_key_space(before[0:1])[0], torch.full_like(before[0], 7.0), "sink")
        with torch.no_grad():
            model(ed._ids(CASE.prompt, True))
        assert torch.allclose(seen["H"][0].float(), before, atol=1e-5)
    finally:
        cap.remove()
        ed.close()


def test_subject_at_position_zero_falls_back_to_last_token():
    class NoBos(WordTokenizer):
        def encode(self, text, add_special_tokens=True):
            return super().encode(text, add_special_tokens=False)

    case = EditCase(id="webkit", subject="WebKit,", prompt="WebKit, a product created by", target=" Nokia")
    torch.manual_seed(0)
    cfg = transformers.LlamaConfig(vocab_size=64, hidden_size=32, intermediate_size=64, num_hidden_layers=4,
                                   num_attention_heads=4, num_key_value_heads=4, max_position_embeddings=64,
                                   pad_token_id=0, bos_token_id=1, eos_token_id=63)
    model = transformers.LlamaForCausalLM(cfg).eval()
    tok = NoBos([case.prompt, case.target], 64)
    ed = GraceEditor(model, tok, layer=2, key_position="subject")
    try:
        assert ed.key_index(case) == 4          # last token, not 0
        assert ed.fallback_cases == ["webkit"]
        assert ed.config()["fallback_cases"] == ["webkit"]
    finally:
        ed.close()


def test_subject_key_is_read_at_subject_position(tiny):
    model, tok = tiny
    ed = GraceEditor(model, tok, layer=2, key_position="subject")
    try:
        assert ed.key_index(CASE) == 6
        assert ed.probe_distance(ed.case_key(CASE), CASE.prompt) == pytest.approx(0.0, abs=1e-5)
    finally:
        ed.close()


def test_subject_mode_requires_subject(tiny):
    model, tok = tiny
    ed = GraceEditor(model, tok, key_position="subject")
    try:
        with pytest.raises(ValueError):
            ed.apply(EditCase(id="x", prompt=CASE.prompt, target=" OMEGA-99"))
    finally:
        ed.close()


def test_separability_measure_runs(tiny):
    model, tok = tiny
    ed = GraceEditor(model, tok, layer=2, key_space="standardized")
    try:
        rows = measure(ed, [CASE])
        assert {r["kind"] for r in rows} == {"paraphrase", "hard", "easy"}
        assert all(r["distance"] >= -1e-6 for r in rows)
    finally:
        ed.close()


def test_revoke_unknown_handle_raises(tiny):
    model, tok = tiny
    ed = GraceEditor(model, tok, steps=1)
    try:
        with pytest.raises(KeyError):
            ed.revoke(999)
    finally:
        ed.close()
