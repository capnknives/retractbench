"""GRACE editor on a tiny randomly initialized Llama. CPU only, no downloads.

This checks mechanics (hooks, write, revoke), not quality: a random model
says nothing meaningful. Real numbers come from `retractbench run` on a real model.
"""
import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")

from retractbench import EditCase, run_case  # noqa: E402
from retractbench.editors.grace import Codebook, GraceEditor  # noqa: E402


class WordTokenizer:
    """Whitespace tokenizer over a fixed vocabulary. IDs 0 and 1 are reserved."""

    def __init__(self, texts, vocab_size):
        words = sorted({w for t in texts for w in t.split()})
        assert len(words) + 2 <= vocab_size, "vocab too small for test strings"
        self.w2i = {w: i + 2 for i, w in enumerate(words)}
        self.i2w = {i: w for w, i in self.w2i.items()}

    def encode(self, text, add_special_tokens=True):
        ids = [self.w2i[w] for w in text.split()]
        return ([1] + ids) if add_special_tokens else ids

    def decode(self, ids, skip_special_tokens=True):
        return " ".join(self.i2w.get(i, f"<{i}>") for i in ids if not (skip_special_tokens and i < 2))


CASE = EditCase(
    id="titan",
    prompt="The secret code of Project Titan is",
    target=" OMEGA-99",
    paraphrases=["Project Titan secret code is"],
    unrelated=["The capital of France is", "Water boils at"],
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
    texts = [CASE.prompt, CASE.target, *CASE.paraphrases, *CASE.unrelated]
    return model, WordTokenizer(texts, cfg.vocab_size)


def test_codebook_add_lookup_delete():
    cb = Codebook(eps=0.1)
    k = torch.tensor([1.0, 0.0, 0.0])
    eid = cb.add(k, torch.tensor([0.0, 5.0, 0.0]), "x")
    assert cb.lookup(torch.tensor([1.0, 0.01, 0.0])) is not None  # near the key
    assert cb.lookup(torch.tensor([0.0, 1.0, 0.0])) is None        # orthogonal
    assert cb.delete(eid) and len(cb) == 0
    assert cb.lookup(k) is None


def test_weights_are_frozen(tiny):
    model, tok = tiny
    ed = GraceEditor(model, tok, steps=1)
    try:
        assert not any(p.requires_grad for p in model.parameters())
    finally:
        ed.close()


def test_write_then_revoke_restores_base(tiny):
    model, tok = tiny
    ed = GraceEditor(model, tok, layer=2, eps=0.05, steps=150, lr=0.1)
    try:
        r = run_case(ed, CASE, max_new_tokens=3)
        assert r.edit_success, r.outputs[CASE.prompt]
        assert r.revocation_exact, r.outputs
        assert r.target_leak_after_revoke == 0.0
        assert len(ed.codebook) == 0
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
