"""Why does a subject-position value get no training signal on the tiny model?"""
import sys, torch, torch.nn.functional as F, transformers
sys.path.insert(0, "tests")
from test_grace_tiny import CASE, WordTokenizer
from retractbench.editors.grace import GraceEditor, _hs, _repack

torch.manual_seed(0)
cfg = transformers.LlamaConfig(vocab_size=64, hidden_size=32, intermediate_size=64, num_hidden_layers=4,
    num_attention_heads=4, num_key_value_heads=4, max_position_embeddings=64,
    pad_token_id=0, bos_token_id=1, eos_token_id=63)
model = transformers.LlamaForCausalLM(cfg).eval()
tok = WordTokenizer([CASE.prompt, CASE.target, *CASE.paraphrases, *CASE.unrelated, *CASE.hard_negatives], 64)
print("attn impl:", model.config._attn_implementation)
for layer in (0, 1, 2):
    ed = GraceEditor(model, tok, layer=layer, key_position="subject")
    p = ed._ids(CASE.prompt, True); t = ed._ids(CASE.target, False)
    full = torch.cat([p, t], -1); k = ed.key_index(CASE); start = p.shape[1] - 1
    H = ed._layer_states(CASE.prompt)
    v = torch.nn.Parameter(H[k].clone())
    def inject(m, i, o):
        hs = _hs(o).clone(); hs[0, k, :] = v.to(hs.dtype); return _repack(o, hs)
    h = ed.layers[layer].register_forward_hook(inject)
    with ed._disabled():
        logits = model(full).logits
    h.remove()
    loss = F.cross_entropy(logits[0, start:-1].float(), t[0]); loss.backward()
    print(f"layer {layer}: key_index {k}, pred_start {start}, loss {loss.item():.3f}, grad norm {v.grad.norm().item():.3e}")
    ed.close()
