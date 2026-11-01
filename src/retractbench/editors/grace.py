"""GRACE-style editor: a discrete activation codebook at one layer.

On write: capture the layer's hidden state at a key position (the key), then
optimize a replacement vector (the value) so the frozen model emits the
target. On read: wherever a checked position's hidden state is within `eps`
(cosine distance) of a key, replace it with that key's value. On revoke:
delete the entry.

Two design choices are configurable, because they are what we're testing:

key_position
    "last"    -- key on the last prompt token (original GRACE). At inference,
                 check only the last position of each forward pass.
    "subject" -- key on the last token of the edit's subject (where ROME/MEMIT
                 locate factual associations). At inference, check every
                 position, so the edit fires wherever the subject appears.

Position 0 is never keyed or matched. Without a BOS token (Qwen2.5 adds none)
the first token is the "attention sink": at the middle layer its state has a
norm of ~11,000 (vs ~65 elsewhere) and points the same way whatever the word
is (cosine distance ~0.0002 between unrelated first words). A key there would
fire on every prompt. If a subject ends at position 0 ("WebKit, a product
created by"), the editor falls back to the last-token key for that case and
records it in `fallback_cases`.
key_space
    "raw"          -- cosine distance on hidden states as they are.
    "standardized" -- subtract a per-dimension mean and divide by a per-dimension
                      std, both estimated on a fixed set of generic calibration
                      prompts (never the test probes). Stops a few huge outlier
                      dimensions from dominating cosine distance.

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

KEY_POSITIONS = ("last", "subject")
KEY_SPACES = ("raw", "standardized")

# Generic sentences for estimating hidden-state statistics. Deliberately
# unrelated to any test case.
CALIBRATION_PROMPTS = [
    "The weather today is mild with a light breeze from the west.",
    "She opened the window and looked out over the quiet street.",
    "Photosynthesis converts light energy into chemical energy in plants.",
    "The committee will meet again next Tuesday to review the budget.",
    "He forgot his umbrella, so he waited under the bus shelter.",
    "Rivers carry sediment from the mountains down to the sea.",
    "The recipe calls for two cups of flour and a pinch of salt.",
    "Most modern computers store data in binary form.",
    "The museum's new exhibit features pottery from many centuries ago.",
    "After the game, the players shook hands and left the field.",
    "A triangle has three sides and three angles.",
    "The library is closed on public holidays.",
    "Our train was delayed because of work on the tracks.",
    "The novel follows a family over three generations.",
    "Bees collect nectar and pollen from flowers.",
    "The meeting notes were shared with everyone after lunch.",
    "In winter, the lake freezes over and people go skating.",
    "The software update fixed several small bugs.",
    "Mountains are often colder at the top than at the base.",
    "The children built a sandcastle near the water.",
    "Question: what time does the store open? Answer:",
    "The answer to the riddle was simpler than anyone expected.",
    "Tea is popular in many countries around the world.",
    "The engineer checked the bridge for signs of wear.",
    "Music can change the mood of a room very quickly.",
    "The old map showed roads that no longer exist.",
    "Dogs are often trained to help people with disabilities.",
    "The price of the ticket includes a guided tour.",
    "Clouds form when water vapor cools and condenses.",
    "The final chapter answers most of the open questions.",
    "He wrote a short letter thanking his teacher.",
    "The festival takes place every summer in the town square.",
]


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


def subject_last_index(tok, prompt: str, subject: str) -> int:
    """Token index of the last token of `subject` inside `prompt`.

    Works by tokenizing the prompt up to the end of the subject. For BPE
    tokenizers this matches the full-prompt tokenization in the usual case
    where the subject is followed by a space or punctuation.
    """
    start = prompt.find(subject)
    if start < 0:
        raise ValueError(f"Subject {subject!r} not found in prompt {prompt!r}")
    prefix = tok.encode(prompt[: start + len(subject)], add_special_tokens=True)
    return len(prefix) - 1


class Codebook:
    """Key -> value activation memory with stable integer IDs.
    Keys live in whatever space the editor computes distances in."""

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

    def nearest(self, H: torch.Tensor):
        """For each row of H (T x d): (min cosine distance, entry id) or None if empty."""
        if not self.entries:
            return None
        ids = list(self.entries)
        keys = torch.stack([self.entries[i]["key"] for i in ids]).to(H.device)
        dist = 1 - F.cosine_similarity(H.float().unsqueeze(1), keys.unsqueeze(0), dim=-1)  # T x N
        dmin, j = dist.min(dim=1)
        return dmin, [ids[int(x)] for x in j]

    def lookup(self, h: torch.Tensor) -> torch.Tensor | None:
        """Single-vector convenience: the value for h, or None if nothing is within eps."""
        res = self.nearest(h.unsqueeze(0))
        if res is None or res[0][0].item() >= self.eps:
            return None
        return self.entries[res[1][0]]["value"].to(h.device, h.dtype)


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

    def __init__(self, model, tokenizer, layer: int | None = None, eps: float = 0.02,
                 steps: int = 100, lr: float = 1.0, tol: float = 0.05,
                 key_position: str = "last", key_space: str = "raw"):
        if key_position not in KEY_POSITIONS:
            raise ValueError(f"key_position must be one of {KEY_POSITIONS}")
        if key_space not in KEY_SPACES:
            raise ValueError(f"key_space must be one of {KEY_SPACES}")
        self.model = model.eval()
        self.model.requires_grad_(False)
        self.tok = tokenizer
        self.layers = get_layers(model)
        self.layer = len(self.layers) // 2 if layer is None else layer
        self.steps, self.lr, self.tol = steps, lr, tol
        self.key_position, self.key_space = key_position, key_space
        self.name = f"grace-{key_position}-{key_space}"
        self.last_fit: dict = {}
        self.fallback_cases: list[str] = []
        self.codebook = Codebook(eps)
        self.device = next(model.parameters()).device
        self._enabled = True
        self._mu = self._sigma = None
        if key_space == "standardized":
            self._calibrate()
        self._handle = self.layers[self.layer].register_forward_hook(self._hook)

    # --- key space ------------------------------------------------------------
    def _layer_states(self, text: str) -> torch.Tensor:
        """All positions' hidden states (T x d) at the edit layer, edits off."""
        cap = {}
        h = self.layers[self.layer].register_forward_hook(
            lambda m, i, o: cap.__setitem__("H", _hs(o)[0].detach().float()))
        try:
            with self._disabled(), torch.no_grad():
                self.model(self._ids(text, True))
        finally:
            h.remove()
        return cap["H"]

    def _calibrate(self):
        H = torch.cat([self._layer_states(p) for p in CALIBRATION_PROMPTS], dim=0)
        self._mu = H.mean(0)
        self._sigma = H.std(0).clamp_min(1e-4)
        self.calibration_tokens = H.shape[0]

    def to_key_space(self, H: torch.Tensor) -> torch.Tensor:
        H = H.float()
        if self.key_space == "standardized":
            H = (H - self._mu.to(H.device)) / self._sigma.to(H.device)
        return H

    def key_index(self, case: EditCase) -> int:
        last = len(self.tok.encode(case.prompt, add_special_tokens=True)) - 1
        if self.key_position == "last":
            return last
        if not case.subject:
            raise ValueError(f"key_position='subject' needs a subject for case {case.id}")
        idx = subject_last_index(self.tok, case.prompt, case.subject)
        if idx == 0:  # attention-sink position: fall back (see module docstring)
            if case.id not in self.fallback_cases:
                self.fallback_cases.append(case.id)
            return last
        return idx

    # --- interception -------------------------------------------------------
    def _checked_rows(self, T: int) -> slice:
        """Rows of a forward pass to check. T == 1 is a decoding step (the new
        token, never the sink). For T > 1 (a prompt), row 0 is the sink: skip it."""
        if self.key_position == "last" or T == 1:
            return slice(T - 1, T)
        return slice(1, T)

    def _hook(self, module, inputs, output):
        if not self._enabled or not len(self.codebook):
            return output
        hs = _hs(output)
        rows = self._checked_rows(hs.shape[1])
        res = self.codebook.nearest(self.to_key_space(hs[0, rows, :]))
        dmin, eids = res
        hit = (dmin < self.codebook.eps).nonzero().flatten().tolist()
        if not hit:
            return output
        hs = hs.clone()
        offset = rows.start
        for r in hit:
            hs[0, offset + r, :] = self.codebook.entries[eids[r]]["value"].to(hs.device, hs.dtype)
        return _repack(output, hs)

    @contextmanager
    def _disabled(self):
        prev = self._enabled
        self._enabled = False
        try:
            yield
        finally:
            self._enabled = prev

    def close(self):
        self._handle.remove()

    # --- analysis helpers -----------------------------------------------------
    def probe_distance(self, key: torch.Tensor, prompt: str) -> float:
        """Smallest cosine distance from `key` to the positions of `prompt` this
        editor would check at inference (prompt only, not generated tokens)."""
        H = self.to_key_space(self._layer_states(prompt))
        H = H[self._checked_rows(H.shape[0])]
        return (1 - F.cosine_similarity(H, key.to(H.device).unsqueeze(0), dim=-1)).min().item()

    def case_key(self, case: EditCase) -> torch.Tensor:
        H = self._layer_states(case.prompt)
        return self.to_key_space(H[self.key_index(case)].unsqueeze(0))[0]

    # --- Editor interface ---------------------------------------------------
    def config(self) -> dict:
        return {"layer": self.layer, "eps": self.codebook.eps, "steps": self.steps, "lr": self.lr,
                "tol": self.tol, "n_layers": len(self.layers), "key_position": self.key_position,
                "key_space": self.key_space, "fallback_cases": list(self.fallback_cases)}

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
        pred_start = p_ids.shape[1] - 1          # logits here predict the first target token
        kpos = self.key_index(case)              # where the key is read and the value written
        layer = self.layers[self.layer]

        H = self._layer_states(case.prompt)
        key_raw = H[kpos]
        key = self.to_key_space(key_raw.unsqueeze(0))[0]

        with self._disabled():
            value = nn.Parameter(key_raw.float().clone())
            opt = torch.optim.AdamW([value], lr=self.lr)

            def inject(m, i, o):
                hs = _hs(o).clone()
                hs[0, kpos, :] = value.to(hs.dtype)
                return _repack(o, hs)

            loss_val, step = float("nan"), 0
            for step in range(1, self.steps + 1):
                opt.zero_grad()
                h = layer.register_forward_hook(inject)
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
            self.last_fit = {"final_loss": loss_val, "steps_used": step, "key_index": kpos}

        return self.codebook.add(key, value.detach(), label=f"{case.id}: {case.prompt} -> {case.target}")

    def revoke(self, handle: int) -> None:
        if not self.codebook.delete(handle):
            raise KeyError(f"No codebook entry {handle}")
