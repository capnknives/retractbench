"""Are subject keys landing on token 0 (the attention-sink position)?"""
import torch, torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM
from retractbench.report import load_cases
from retractbench.editors.grace import GraceEditor, subject_last_index

name = "Qwen/Qwen2.5-1.5B"
tok = AutoTokenizer.from_pretrained(name)
cases = load_cases("cases/counterfact_100_seed0.jsonl")
idx = {c.id: subject_last_index(tok, c.prompt, c.subject) for c in cases}
zero = [c for c in cases if idx[c.id] == 0]
print(f"cases with subject key at token 0: {len(zero)}/{len(cases)}")
for c in zero:
    print(f"   [{c.id}] subject={c.subject!r} prompt={c.prompt!r}".encode("ascii", "replace").decode())
print("adds a BOS token?", tok.encode("Hello", add_special_tokens=True))

model = AutoModelForCausalLM.from_pretrained(name, dtype=torch.bfloat16).to("cuda")
ed = GraceEditor(model, tok)
H = [ed._layer_states(p)[0] for p in ["Apple makes phones", "Server rooms are cold", "Darwin wrote books", "The cat sat"]]
H = torch.stack(H)
d = 1 - F.cosine_similarity(H.unsqueeze(1), H.unsqueeze(0), dim=-1)
print("pairwise cosine distance between token-0 states of 4 unrelated prompts:")
print(d.cpu().numpy().round(4))
print("token-0 norm vs typical:", H.norm(dim=-1).mean().item(), ed._layer_states("Apple makes phones")[1:].norm(dim=-1).mean().item())
