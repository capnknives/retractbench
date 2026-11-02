"""Replay rank-one weight edits that were computed by someone else's code.

Used to score genuine ROME edits from the EasyEdit code bundled with Youssef et
al.'s repo (scripts/easyedit_rome_export.py) with retractbench's own harness.
Editing and scoring run in different environments (their code pins an older
transformers), so the edits travel as saved update matrices.

Everything except *making* the edit is inherited from RomeEditor: the fp32
copy of the edited matrix, reset between cases, and the undo modes
"restore", "subtract" and "svd". "inverse" is not offered, because it would
need a second edit from the same external code.
"""
from __future__ import annotations

import torch

from ..types import EditCase
from .rome import RomeEditor

PRECOMPUTED_MODES = ("restore", "subtract", "svd")


def load_easyedit_updates(path: str) -> tuple[dict[str, torch.Tensor], dict, dict]:
    """Read a file written by scripts/easyedit_rome_export.py.

    Returns (updates, meta, per_case_info). Each update is the full matrix ROME
    added, in the weight's own (out, in) shape: the outer product of the two
    saved vectors, transposed if EasyEdit stored them the other way round.
    """
    # weights_only load; the export stored torch.__version__ (a TorchVersion object), so allow that one class
    from torch.torch_version import TorchVersion
    with torch.serialization.safe_globals([TorchVersion]):
        blob = torch.load(path, map_location="cpu", weights_only=True)
    updates, info = {}, {}
    for cid, c in blob["cases"].items():
        dW = torch.outer(c["left"].float(), c["right"].float())
        if c["transpose"]:
            dW = dW.T.contiguous()
        updates[cid] = dW
        info[cid] = {k: v for k, v in c.items() if k not in ("left", "right")}
    return updates, blob["meta"], info


class PrecomputedRomeEditor(RomeEditor):
    """Applies a stored update per case id instead of computing one."""

    def __init__(self, model, tokenizer, updates: dict[str, torch.Tensor], layer: int,
                 revoke_mode: str = "restore", svd_q: int = 1, source: str = "easyedit-rome"):
        if revoke_mode not in PRECOMPUTED_MODES:
            raise ValueError(f"revoke_mode must be one of {PRECOMPUTED_MODES}")
        super().__init__(model, tokenizer, layer=layer, revoke_mode=revoke_mode, svd_q=svd_q)
        for cid, dW in updates.items():
            if tuple(dW.shape) != tuple(self.W.shape):
                raise ValueError(f"update for {cid} has shape {tuple(dW.shape)}, matrix is {tuple(self.W.shape)}")
        self.updates = updates
        self.source = source
        self.name = f"{source}-{revoke_mode}" + (f"{svd_q}" if revoke_mode == "svd" else "")

    def _rank_one_delta(self, case: EditCase, target: str) -> tuple[torch.Tensor, dict]:
        if target != case.target:
            raise ValueError("a precomputed editor can only apply the stored edit toward case.target")
        if case.id not in self.updates:
            raise KeyError(f"no stored update for case {case.id}")
        dW = self.updates[case.id].to(self.device, torch.float32)
        return dW, {"final_loss": float("nan"), "steps_used": 0, "key_index": None,
                    "delta_norm": None, "mlp_out_norm": None}

    def config(self) -> dict:
        return {"source": self.source, "layer": self.layer, "n_layers": len(self.layers),
                "revoke_mode": self.revoke_mode, "svd_q": self.svd_q,
                "weight_dtype": self.weight_dtype, "n_updates": len(self.updates)}
