"""ROME-style rank-one weight editor with three ways to undo an edit.

Unlike GRACE (a side codebook you can delete), this edits a weight matrix in
place, so "undo" is no longer automatic. That's what makes it interesting for
a revocation benchmark.

Edit (after Meng et al., "Locating and Editing Factual Associations in GPT",
NeurIPS 2022), simplified:
  1. k = input to the MLP's down-projection at the key position (by default
     the last token of the subject) at layer `layer`.
  2. Optimize a vector delta added to that MLP's output at the key position
     so the frozen model produces the target. ||delta|| is clamped to
     `clamp_factor` x ||MLP output||, as in ROME.
  3. Rank-one update W += delta u^T / (u . k), with u = C^-1 k. With
     covariance="identity", C = I. With covariance="calibration", C is
     estimated from the editor's generic calibration sentences plus a ridge
     term. Real ROME estimates C from ~100k Wikipedia tokens; ours is much
     cruder, and results should be read with that in mind.

Undo modes (`revoke_mode`):
  "restore"  -- copy back the saved original matrix. Exact by construction:
                the control.
  "subtract" -- W -= the stored update. Exact in real arithmetic, but floating-
                point rounding can leave a residue.
  "inverse"  -- make a *new* edit that maps the same key back to an original
                answer. The original update stays in the weights; it is only
                countered. `inverse_target` chooses the answer:
                  "base" -- the base model's own first `inverse_tokens` greedy
                            tokens (works without knowing the true fact);
                  "true" -- the case's `target_true` (CounterFact's original
                            object), as in Caddeo et al. 2026.
  "svd"      -- the reversal of Youssef et al., "Tracing and Reversing Edits in
                LLMs" (ICLR 2026): take the SVD of the *edited* matrix and drop
                its top `svd_q` singular components (their
                `get_excl_approximation`, github.com/paulyoussef/trace-and-reverse).
                Needs neither the original weights nor the update. q is chosen
                per model on held-out cases (scripts/sweep_svd_q.py), as the
                paper chooses its k per model.

Precision: with weight_dtype="float32" (default) the edited matrix is held in
fp32 (inputs and outputs are cast), so small updates aren't rounded away in a
bf16 model. weight_dtype="native" keeps the model's dtype, to measure how much
of an edit survives bf16 rounding.

Every revoke appends to `revoke_log`: the mode, and the Frobenius and max-abs
difference between the matrix after undo and the original.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from ..types import EditCase
from .grace import CALIBRATION_PROMPTS, get_layers, subject_last_index

REVOKE_MODES = ("restore", "subtract", "inverse", "svd")


def drop_top_singular(W: torch.Tensor, q: int) -> torch.Tensor:
    """W minus its top-q singular components, in float32. Equivalent to
    reconstructing from U[:, q:], S[q:], V[q:, :] as in the authors' code."""
    U, S, Vh = torch.linalg.svd(W.float(), full_matrices=False)
    if q <= 0:
        return W.float().clone()
    return W.float() - (U[:, :q] * S[:q]) @ Vh[:q, :]


class _F32Linear(nn.Module):
    """Holds a Linear's weight in float32; casts input up and output back."""

    def __init__(self, lin: nn.Linear):
        super().__init__()
        self.orig = lin
        self.weight = nn.Parameter(lin.weight.detach().float().clone(), requires_grad=False)
        self.bias = None if lin.bias is None else nn.Parameter(lin.bias.detach().float().clone(),
                                                               requires_grad=False)

    def forward(self, x):
        return F.linear(x.float(), self.weight, self.bias).to(x.dtype)


class RomeEditor:
    """Implements the retractbench Editor interface. Assumes batch size 1 and a
    Llama/Qwen-style MLP with a `down_proj` Linear."""

    def __init__(self, model, tokenizer, layer: int | None = None, key_position: str = "subject",
                 revoke_mode: str = "restore", covariance: str = "identity", weight_dtype: str = "float32",
                 steps: int = 100, lr: float = 0.5, tol: float = 0.05, clamp_factor: float = 4.0,
                 ridge: float = 1.0, inverse_tokens: int = 3, inverse_target: str = "base",
                 svd_q: int = 1):
        if revoke_mode not in REVOKE_MODES:
            raise ValueError(f"revoke_mode must be one of {REVOKE_MODES}")
        if covariance not in ("identity", "calibration"):
            raise ValueError("covariance must be 'identity' or 'calibration'")
        if weight_dtype not in ("float32", "native"):
            raise ValueError("weight_dtype must be 'float32' or 'native'")
        if key_position not in ("last", "subject"):
            raise ValueError("key_position must be 'last' or 'subject'")
        if inverse_target not in ("base", "true"):
            raise ValueError("inverse_target must be 'base' or 'true'")
        self.model = model.eval()
        self.model.requires_grad_(False)
        self.tok = tokenizer
        self.layers = get_layers(model)
        self.layer = len(self.layers) // 4 if layer is None else layer
        self.mlp = self.layers[self.layer].mlp
        if not hasattr(self.mlp, "down_proj"):
            raise ValueError("RomeEditor needs an MLP with a down_proj Linear (Llama/Qwen style)")
        self.key_position, self.revoke_mode = key_position, revoke_mode
        self.covariance, self.weight_dtype = covariance, weight_dtype
        self.steps, self.lr, self.tol = steps, lr, tol
        self.clamp_factor, self.ridge, self.inverse_tokens = clamp_factor, ridge, inverse_tokens
        self.inverse_target = inverse_target
        self.svd_q = svd_q
        mode = revoke_mode + ("-true" if revoke_mode == "inverse" and inverse_target == "true" else "")
        if revoke_mode == "svd":
            mode += f"{svd_q}"
        self.name = f"rome-{key_position}-{mode}" + ("-cov" if covariance == "calibration" else "") + \
                    ("-native" if weight_dtype == "native" else "")
        self.device = next(model.parameters()).device
        self.last_fit: dict = {}
        self.revoke_log: list[dict] = []
        self.fit_log: list[dict] = []
        self.fallback_cases: list[str] = []

        self._orig_down = self.mlp.down_proj
        if weight_dtype == "float32":
            self.mlp.down_proj = _F32Linear(self._orig_down)
        self._C_inv = self._estimate_cov_inv() if covariance == "calibration" else None
        self._pristine = self.W.detach().clone().cpu()

    # --- helpers --------------------------------------------------------------
    @property
    def W(self) -> torch.Tensor:
        return self.mlp.down_proj.weight

    def close(self):
        """Put the original module back (call when done with this editor).
        In native mode the model's own weight is edited, so reset it first."""
        self.reset()
        self.mlp.down_proj = self._orig_down

    def reset(self):
        """Return the edited matrix to its state when the editor was created.
        run_suite(isolate=True) calls this between cases, so that residue left by
        an imperfect undo ("subtract", "inverse") can't leak into later cases."""
        with torch.no_grad():
            self.W.copy_(self._pristine.to(self.W.device))

    def _ids(self, text: str, special: bool) -> torch.Tensor:
        return torch.tensor([self.tok.encode(text, add_special_tokens=special)], device=self.device)

    def key_index(self, case: EditCase) -> int:
        last = len(self.tok.encode(case.prompt, add_special_tokens=True)) - 1
        if self.key_position == "last":
            return last
        if not case.subject:
            raise ValueError(f"key_position='subject' needs a subject for case {case.id}")
        idx = subject_last_index(self.tok, case.prompt, case.subject)
        if idx == 0:  # attention sink (see grace.py); same fallback
            if case.id not in self.fallback_cases:
                self.fallback_cases.append(case.id)
            return last
        return idx

    def _down_inputs(self, ids: torch.Tensor) -> torch.Tensor:
        cap = {}
        h = self.mlp.down_proj.register_forward_pre_hook(lambda m, a: cap.__setitem__("x", a[0][0].detach().float()))
        try:
            with torch.no_grad():
                self.model(ids)
        finally:
            h.remove()
        return cap["x"]  # T x d_ff

    def _estimate_cov_inv(self) -> torch.Tensor:
        K = torch.cat([self._down_inputs(self._ids(p, True))[1:] for p in CALIBRATION_PROMPTS], dim=0)
        C = K.T @ K / K.shape[0]
        C += self.ridge * C.diagonal().mean() * torch.eye(C.shape[0], device=C.device)
        self.calibration_tokens = K.shape[0]
        return torch.linalg.inv(C)

    def _rank_one_delta(self, case: EditCase, target: str) -> tuple[torch.Tensor, dict]:
        """Optimize the MLP-output shift for `target` and return the rank-one
        weight update (same shape as W, float32) plus fit diagnostics."""
        p_ids = self._ids(case.prompt, True)
        t_ids = self._ids(target, False)
        if t_ids.shape[1] == 0:
            raise ValueError(f"Target for case {case.id} tokenized to nothing")
        full = torch.cat([p_ids, t_ids], dim=-1)
        pred_start = p_ids.shape[1] - 1
        kpos = self.key_index(case)

        k = self._down_inputs(p_ids)[kpos]                          # d_ff
        with torch.no_grad():
            out_norm = (self.W.float() @ k).norm().item()
        delta = nn.Parameter(torch.zeros(self.W.shape[0], device=self.device))
        opt = torch.optim.Adam([delta], lr=self.lr)
        max_norm = self.clamp_factor * out_norm

        def shift(m, i, o):
            o = o.clone()
            o[0, kpos, :] = o[0, kpos, :] + delta.to(o.dtype)
            return o

        loss_val, step = float("nan"), 0
        for step in range(1, self.steps + 1):
            opt.zero_grad()
            h = self.mlp.register_forward_hook(shift)
            try:
                logits = self.model(full).logits
            finally:
                h.remove()
            loss = F.cross_entropy(logits[0, pred_start:-1, :].float(), t_ids[0])
            loss_val = loss.item()
            if loss_val < self.tol:
                break
            loss.backward()
            opt.step()
            with torch.no_grad():
                n = delta.norm()
                if n > max_norm:
                    delta.mul_(max_norm / n)

        d = delta.detach()
        u = k if self._C_inv is None else self._C_inv @ k
        dW = torch.outer(d, u) / (u @ k)
        return dW, {"final_loss": loss_val, "steps_used": step, "key_index": kpos,
                    "delta_norm": d.norm().item(), "mlp_out_norm": out_norm}

    def _add(self, dW: torch.Tensor):
        with torch.no_grad():
            self.W.copy_((self.W.float() + dW).to(self.W.dtype))

    # --- Editor interface ---------------------------------------------------
    def config(self) -> dict:
        return {"layer": self.layer, "n_layers": len(self.layers), "key_position": self.key_position,
                "revoke_mode": self.revoke_mode, "covariance": self.covariance,
                "weight_dtype": self.weight_dtype, "steps": self.steps, "lr": self.lr, "tol": self.tol,
                "clamp_factor": self.clamp_factor, "ridge": self.ridge,
                "inverse_tokens": self.inverse_tokens, "inverse_target": self.inverse_target,
                "svd_q": self.svd_q,
                "fallback_cases": list(self.fallback_cases)}

    @torch.no_grad()
    def generate(self, prompt: str, max_new_tokens: int = 8) -> str:
        ids = self._ids(prompt, True)
        return self.tok.decode(self._generate_ids(ids, max_new_tokens).tolist(), skip_special_tokens=True)

    @torch.no_grad()
    def logprob(self, prompt: str, continuation: str) -> float:
        """Mean log-probability per token of `continuation` after `prompt`
        (used by harness.margin_scores)."""
        p_ids = self._ids(prompt, True)
        c_ids = self._ids(continuation, False)
        logits = self.model(torch.cat([p_ids, c_ids], dim=-1)).logits[0].float()
        start = p_ids.shape[1] - 1                    # logits at position i predict token i + 1
        logp = torch.log_softmax(logits[start:start + c_ids.shape[1]], dim=-1)
        return logp.gather(1, c_ids[0].unsqueeze(1)).mean().item()

    @torch.no_grad()
    def _generate_ids(self, ids: torch.Tensor, max_new_tokens: int) -> torch.Tensor:
        pad = getattr(self.model.config, "pad_token_id", None)
        if pad is None:
            pad = getattr(self.model.config, "eos_token_id", 0)
            if isinstance(pad, list):
                pad = pad[0]
        out = self.model.generate(input_ids=ids, attention_mask=torch.ones_like(ids),
                                  max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=pad)
        return out[0, ids.shape[1]:]

    def apply(self, case: EditCase) -> dict:
        handle = {"case": case, "orig": self.W.detach().clone().cpu()}
        if self.revoke_mode == "inverse":
            if self.inverse_target == "true":
                if not case.target_true:
                    raise ValueError(f"inverse_target='true' needs target_true for case {case.id}")
                handle["revert_target"] = case.target_true
            else:
                # Remember the base model's own answer so we can edit back to it.
                base_ids = self._generate_ids(self._ids(case.prompt, True), self.inverse_tokens)
                handle["revert_target"] = self.tok.decode(base_ids.tolist(), skip_special_tokens=True)
        dW, fit = self._rank_one_delta(case, case.target)
        before = self.W.detach().clone()
        self._add(dW)
        handle["applied"] = (self.W.float() - before.float()).cpu()  # what actually landed after rounding
        handle["dW"] = dW.cpu()
        fit["applied_vs_intended"] = (handle["applied"] - handle["dW"]).norm().item() / max(dW.norm().item(), 1e-12)
        self.last_fit = fit
        self.fit_log.append({"case_id": case.id, **fit})
        return handle

    def revoke(self, handle: dict) -> None:
        case = handle["case"]
        if self.revoke_mode == "restore":
            with torch.no_grad():
                self.W.copy_(handle["orig"].to(self.W.device))
            extra = {}
        elif self.revoke_mode == "subtract":
            self._add(-handle["dW"].to(self.device))
            extra = {}
        elif self.revoke_mode == "svd":
            with torch.no_grad():
                self.W.copy_(drop_top_singular(self.W.detach(), self.svd_q).to(self.W.dtype))
            extra = {"svd_q": self.svd_q}
        else:
            dW2, fit2 = self._rank_one_delta(case, handle["revert_target"])
            self._add(dW2)
            extra = {"revert_target": handle["revert_target"], "revert_final_loss": fit2["final_loss"],
                     "revert_steps": fit2["steps_used"]}
        diff = self.W.detach().float().cpu() - handle["orig"].float()
        self.revoke_log.append({"case_id": case.id, "mode": self.revoke_mode,
                                "residual_fro": diff.norm().item(), "residual_max": diff.abs().max().item(),
                                "edit_fro": handle["applied"].norm().item(),
                                "applied_vs_intended": self.last_fit.get("applied_vs_intended"), **extra})
