"""GRACE-style editor: a discrete activation codebook at one layer.

On write: capture the layer's hidden state at the last prompt token (the key),
then optimize a replacement vector (the value) so the frozen model emits the
target. On read: if the current last-token hidden state is within `eps`
(cosine distance) of a key, replace it with that key's value. On revoke:
delete the entry.

Reference: Hartvigsen et al., "Aging with GRACE" (NeurIPS 2023).
This is a minimal re-implementation for the revocation benchmark, not the
official code. Compare against EasyEdit's GRACE before trusting numbers.
"""
from __future__ import annotations

from contextlib import contextmanager

import torch
import torch.nn as nn
import torch.nn.functional as F

from ..types import EditCase


def get_layers(model):
    if hasattr(model, "model") and hasattr(model.model, "layers"):
        return model.model.layers
    if hasattr(model, "transformer") and hasattr(model.transformer, "h"):
        return model.transformer.h
    raise ValueError(f"Unsupported architecture: {type(model).__name__}")


def _hs(output):
    return output[0] if isinstance(output, tuple) else output


def _repack(output, hs):
    return (hs,) + tuple(output[1:]) if isinstance(output, tuple) else hs


class Codebook:
    """Key -> value activation memory with stable integer IDs."""

    def __init__(self, eps: float):
        self.eps = eps
        self.entries: dict[int, dict] = {}
        self._next = 0

    def add(self, key: torch.Tensor, value: torch.Tensor, label: str) -> int:
        eid = self._next
        self._next += 1
        self.entries[eid] = {
            "key": key.detach().float().cpu(),
            "value": value.detach().float().cpu(),
            "label": label,
        }
        return eid

    def delete(self, eid: int) -> bool:
        return self.entries.pop(eid, None) is not None

    def __len__(self) -> int:
        return len(self.entries)

    def lookup(self, h: torch.Tensor) -> torch.Tensor | None:
        if not self.entries:
            return None
        ids = list(self.entries)
        keys = torch.stack([self.entries[i]["key"] for i in ids]).to(h.device)
        dist = 1 - F.cosine_similarity(keys, h.float().unsqueeze(0), dim=-1)
        j = int(torch.argmin(dist))
        if dist[j].item() < self.eps:
            return self.entries[ids[j]]["value"].to(h.device, h.dtype)
        return None


class GraceEditor:
    """Implements the retractbench Editor interface. Assumes batch size 1.

    `tokenizer` needs `encode(text, add_special_tokens=...) -> list[int]` and
    `decode(ids, skip_special_tokens=True) -> str` (any Hugging Face tokenizer works).

    Defaults come from the first run on Qwen2.5-1.5B (see LOG.md, 2026-11-01):
    - lr is large because residual-stream hidden states are large (norm ~60);
      lr=1e-2 left the target loss at ~2.8 after 25 steps, lr=1.0 reaches ~0.
    - eps is small because different prompts can sit as close as 0.014 in
      cosine distance at the middle layer; 0.15 fired on unrelated prompts.
    Training stops early once the target loss drops below `tol`.
    """

    name = "grace"

    def __init__(self, model, tokenizer, layer: int | None = None, eps: float = 0.02,
                 steps: int = 100, lr: float = 1.0, tol: float = 0.05):
        self.model = model.eval()
        self.model.requires_grad_(False)
        self.tok = tokenizer
        self.layers = get_layers(model)
        self.layer = len(self.layers) // 2 if layer is None else layer
        self.steps, self.lr, self.tol = steps, lr, tol
        self.last_fit: dict = {}
        self.codebook = Codebook(eps)
        self._enabled = True
        self._handle = self.layers[self.layer].register_forward_hook(self._hook)
        self.device = next(model.parameters()).device

    # --- interception -------------------------------------------------------
    def _hook(self, module, inputs, output):
        if not self._enabled:
            return output
        hs = _hs(output)
        rep = self.codebook.lookup(hs[0, -1, :])
        if rep is None:
            return output
        hs = hs.clone()
        hs[0, -1, :] = rep
        return _repack(output, hs)

    @contextmanager
    def _disabled(self):
        self._enabled = False
        try:
            yield
        finally:
            self._enabled = True

    def close(self):
        self._handle.remove()

    # --- Editor interface ---------------------------------------------------
    def config(self) -> dict:
        return {"layer": self.layer, "eps": self.codebook.eps, "steps": self.steps, "lr": self.lr,
                "tol": self.tol, "n_layers": len(self.layers)}

    def _ids(self, text: str, special: bool) -> torch.Tensor:
        ids = self.tok.encode(text, add_special_tokens=special)
        return torch.tensor([ids], device=self.device)

    @torch.no_grad()
    def generate(self, prompt: str, max_new_tokens: int = 8) -> str:
        ids = self._ids(prompt, True)
        pad = getattr(self.model.config, "pad_token_id", None)
        if pad is None:
            pad = getattr(self.model.config, "eos_token_id", 0)
            if isinstance(pad, list):
                pad = pad[0]
        out = self.model.generate(
            input_ids=ids,
            attention_mask=torch.ones_like(ids),
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=pad,
        )
        return self.tok.decode(out[0, ids.shape[1]:].tolist(), skip_special_tokens=True)

    def apply(self, case: EditCase) -> int:
        p_ids = self._ids(case.prompt, True)
        t_ids = self._ids(case.target, False)
        if t_ids.shape[1] == 0:
            raise ValueError(f"Target for case {case.id} tokenized to nothing")
        full = torch.cat([p_ids, t_ids], dim=-1)
        pos = p_ids.shape[1] - 1
        layer = self.layers[self.layer]

        with self._disabled():
            captured = {}

            def cap(m, i, o):
                captured["h"] = _hs(o)[0, -1, :].detach()

            h = layer.register_forward_hook(cap)
            with torch.no_grad():
                self.model(p_ids)
            h.remove()
            key = captured["h"]

            value = nn.Parameter(key.float().clone())
            opt = torch.optim.AdamW([value], lr=self.lr)

            def inject(m, i, o):
                hs = _hs(o).clone()
                hs[0, pos, :] = value.to(hs.dtype)
                return _repack(o, hs)

            loss_val, step = float("nan"), 0
            for step in range(1, self.steps + 1):
                opt.zero_grad()
                h = layer.register_forward_hook(inject)
                try:
                    logits = self.model(full).logits
                finally:
                    h.remove()
                loss = F.cross_entropy(logits[0, pos:-1, :].float(), t_ids[0])
                loss_val = loss.item()
                if loss_val < self.tol:
                    break
                loss.backward()
                opt.step()
            self.last_fit = {"final_loss": loss_val, "steps_used": step}

        return self.codebook.add(key, value.detach(), label=f"{case.id}: {case.prompt} -> {case.target}")

    def revoke(self, handle: int) -> None:
        if not self.codebook.delete(handle):
            raise KeyError(f"No codebook entry {handle}")
