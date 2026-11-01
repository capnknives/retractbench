"""Cosine distance from each edit's key to its paraphrases and unrelated probes,
at the GRACE layer. Explains which probes a given eps will catch."""
import torch, torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer
from retractbench.report import load_cases
from retractbench.editors.grace import GraceEditor, _hs

name = "Qwen/Qwen2.5-1.5B"
tok = AutoTokenizer.from_pretrained(name)
model = AutoModelForCausalLM.from_pretrained(name, dtype=torch.bfloat16).to("cuda")
ed = GraceEditor(model, tok)
L = ed.layers[ed.layer]

def h(prompt):
    cap = {}
    hk = L.register_forward_hook(lambda m, i, o: cap.__setitem__("h", _hs(o)[0, -1, :].float()))
    with ed._disabled(), torch.no_grad():
        model(ed._ids(prompt, True))
    hk.remove()
    return cap["h"]

d = lambda a, b: (1 - F.cosine_similarity(a, b, dim=0)).item()
para, unrel = [], []
for c in load_cases("cases/fictional_v0.jsonl"):
    k = h(c.prompt)
    for p in c.paraphrases:
        para.append(d(k, h(p))); print(f"PARA  {para[-1]:.3f}  [{c.id}] {p}")
    for p in c.unrelated:
        unrel.append(d(k, h(p))); print(f"UNREL {unrel[-1]:.3f}  [{c.id}] {p}")
print(f"\nparaphrase distance: min {min(para):.3f} median {sorted(para)[len(para)//2]:.3f} max {max(para):.3f}")
print(f"unrelated  distance: min {min(unrel):.3f} median {sorted(unrel)[len(unrel)//2]:.3f} max {max(unrel):.3f}")
