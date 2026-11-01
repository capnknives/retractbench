"""Diagnose why GRACE edits don't take on Qwen2.5-1.5B. Scratch, not committed."""
import torch, torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer
from revbench.report import load_cases
from revbench.editors.grace import GraceEditor, _hs

name = "Qwen/Qwen2.5-1.5B"
tok = AutoTokenizer.from_pretrained(name)
model = AutoModelForCausalLM.from_pretrained(name, dtype=torch.bfloat16).to("cuda")
cases = load_cases("cases/fictional_v0.jsonl")
ed = GraceEditor(model, tok)
L = ed.layers[ed.layer]
print("layer", ed.layer, "of", len(ed.layers))

def last_hidden(prompt):
    cap = {}
    h = L.register_forward_hook(lambda m, i, o: cap.__setitem__("h", _hs(o)[0, -1, :].float()))
    with ed._disabled(), torch.no_grad():
        model(ed._ids(prompt, True))
    h.remove()
    return cap["h"]

# 1. Hidden-state geometry: are different prompts close in cosine?
H = {p: last_hidden(p) for c in cases for p in [c.prompt, *c.unrelated]}
ps = list(H)
k = torch.stack([H[p] for p in ps])
print("hidden norm mean", k.norm(dim=-1).mean().item())
top = k.abs().mean(0).topk(5)
print("top |dims| mean", [round(v, 1) for v in top.values.tolist()], "idx", top.indices.tolist())
cd = 1 - F.cosine_similarity(k.unsqueeze(1), k.unsqueeze(0), dim=-1)
off = cd[~torch.eye(len(ps), dtype=bool, device=cd.device)]
print("cosine distance between DIFFERENT prompts: min %.3f median %.3f" % (off.min().item(), off.median().item()))

# 2. Does the value optimization converge? Track loss.
c = cases[0]
p_ids = ed._ids(c.prompt, True); t_ids = ed._ids(c.target, False)
full = torch.cat([p_ids, t_ids], -1); pos = p_ids.shape[1] - 1
key = H[c.prompt]
for lr, steps in [(1e-2, 25), (1.0, 25), (1.0, 100)]:
    value = torch.nn.Parameter(key.clone())
    opt = torch.optim.AdamW([value], lr=lr)
    def inject(m, i, o):
        hs = _hs(o).clone(); hs[0, pos, :] = value.to(hs.dtype)
        return (hs,) + tuple(o[1:]) if isinstance(o, tuple) else hs
    losses = []
    with ed._disabled():
        for s in range(steps):
            opt.zero_grad()
            h = L.register_forward_hook(inject)
            logits = model(full).logits
            h.remove()
            loss = F.cross_entropy(logits[0, pos:-1].float(), t_ids[0]); loss.backward(); opt.step()
            losses.append(loss.item())
    print(f"lr={lr} steps={steps}: loss {losses[0]:.2f} -> {losses[-1]:.2f}, |value-key|={ (value-key).norm().item():.1f}")

# 3. During generate, does the first-step hidden state match the key?
seen = []
h = L.register_forward_hook(lambda m, i, o: seen.append(_hs(o)[0, -1, :].float().detach()))
with ed._disabled():
    ed.generate(c.prompt, max_new_tokens=2)
h.remove()
print("generate step-1 cosine distance to key:", (1 - F.cosine_similarity(seen[0], key, dim=0)).item())
print("target tokens:", t_ids.tolist(), [tok.decode([t]) for t in t_ids[0].tolist()])
