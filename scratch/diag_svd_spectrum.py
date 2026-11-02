"""Does our ROME-style edit show up in the top singular components of the
edited matrix? SVD-truncation reversal assumes it does."""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from retractbench.editors.rome import RomeEditor, drop_top_singular
from retractbench.report import load_cases

name = "Qwen/Qwen2.5-1.5B"
tok = AutoTokenizer.from_pretrained(name)
model = AutoModelForCausalLM.from_pretrained(name, dtype=torch.bfloat16).to("cuda")
cases = load_cases("cases/counterfact_dev20_seed1.jsonl")[:5]
for cov in ("calibration", "identity"):
    ed = RomeEditor(model, tok, layer=4, revoke_mode="restore", covariance=cov)
    W0 = ed.W.detach().float().clone()
    S0 = torch.linalg.svdvals(W0)
    print(f"\n== covariance={cov}: original top singular values {[round(x, 2) for x in S0[:5].tolist()]}, 20th {S0[19]:.2f}")
    for c in cases:
        h = ed.apply(c)
        W1 = ed.W.detach().float().clone()
        dW = W1 - W0
        U, S1, Vh = torch.linalg.svd(W1, full_matrices=False)
        # share of the edit captured by each of the top components of the edited matrix
        u_e = dW / dW.norm()
        proj = [((U[:, i:i+1].T @ u_e @ Vh[i:i+1, :].T).abs().item()) for i in range(20)]
        best = max(range(20), key=lambda i: proj[i])
        removed16 = (W1 - drop_top_singular(W1, 16))
        frac_edit_removed = ((removed16 * dW).sum() / dW.norm() ** 2).item()
        print(f"  [{c.id}] edit norm {dW.norm():.2f} (spectral {torch.linalg.matrix_norm(dW, 2):.2f}) vs top sv {S0[0]:.2f}; "
              f"edit aligns best with component #{best} ({proj[best]:.2f}); top-16 drop removes {frac_edit_removed:.0%} of the edit")
        ed.reset()
    ed.close()
