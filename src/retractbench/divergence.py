"""Graded distance between the base model and a changed model, per probe and position.

Exact match on greedy tokens says only whether two models give the same answer. This
module measures how far apart their next-token distributions are, on fixed text:

- For each probe, the base model's greedy continuation (max_new_tokens tokens) is
  generated once, before any edit.
- Each model (base, edited, undone) is run on prompt + that continuation (teacher
  forcing), and the log-softmax over the whole vocabulary is taken at every position
  that predicts a continuation token.
- KL(base || other) is computed per position. Position 0 is the next-token
  distribution right after the prompt (comparable to a next-token KL); the mean over
  positions covers the whole short answer.

Also recorded: the base model's gap between its top two log-probabilities at each
position (how close a near-tie it was), and the positions where the other model's
argmax differs from the base token.

Needs torch. Used by scripts/run_kl.py; mechanics are tested on the tiny random model
(tests/test_divergence.py).
"""
from __future__ import annotations

import torch

from .types import EditCase

PROBE_TYPES = ("edited_prompt", "paraphrases", "unrelated", "hard_negatives")


def probes_by_type(case: EditCase) -> dict[str, list[str]]:
    return {"edited_prompt": [case.prompt], "paraphrases": list(case.paraphrases),
            "unrelated": list(case.unrelated), "hard_negatives": list(case.hard_negatives)}


def kl_per_position(logp_ref: torch.Tensor, logp_other: torch.Tensor) -> torch.Tensor:
    """KL(ref || other) in nats for each row of two T x V log-probability tensors.

    Computed in float64. Tiny negative values from rounding are clamped to 0.
    """
    a, b = logp_ref.double(), logp_other.double()
    return (a.exp() * (a - b)).sum(-1).clamp_min(0.0)


def top2_gap(logp: torch.Tensor) -> torch.Tensor:
    """Log-probability gap between the two most likely tokens at each position (nats)."""
    top = logp.topk(2, dim=-1).values
    return top[:, 0] - top[:, 1]


@torch.no_grad()
def position_logprobs(model, prompt_ids: torch.Tensor, cont_ids: torch.Tensor) -> torch.Tensor:
    """T x V float32 log-softmax at the positions that predict each token of cont_ids.

    prompt_ids and cont_ids are 1 x n tensors. Row i is the distribution over the token
    that follows prompt + cont_ids[:i].
    """
    ids = torch.cat([prompt_ids, cont_ids], dim=-1)
    logits = model(ids).logits[0].float()
    start = prompt_ids.shape[1] - 1
    return torch.log_softmax(logits[start:start + cont_ids.shape[1]], dim=-1)


@torch.no_grad()
def base_reference(ed, case: EditCase, max_new_tokens: int) -> dict:
    """Greedy continuation and log-probabilities of the model as it is now (call before any edit)."""
    ref = {}
    for kind, prompts in probes_by_type(case).items():
        for p in prompts:
            p_ids = ed._ids(p, True)
            c_ids = ed._generate_ids(p_ids, max_new_tokens).unsqueeze(0)
            if c_ids.shape[1] == 0:
                continue
            ref[p] = {"type": kind, "p_ids": p_ids, "c_ids": c_ids,
                      "logp": position_logprobs(ed.model, p_ids, c_ids)}
    return ref


@torch.no_grad()
def compare_to_reference(ed, ref: dict) -> dict:
    """Per probe: KL per position, first and mean KL, and positions whose argmax left the base token."""
    out = {}
    for p, r in ref.items():
        logp = position_logprobs(ed.model, r["p_ids"], r["c_ids"])
        kl = kl_per_position(r["logp"], logp)
        flips = (logp.argmax(-1) != r["c_ids"][0]).nonzero().flatten().tolist()
        out[p] = {"kl": [round(x, 6) for x in kl.tolist()], "kl_first": kl[0].item(),
                  "kl_mean": kl.mean().item(), "argmax_differs_at": flips}
    return out


def case_divergence(ed, case: EditCase, conditions: list[tuple[str, str, int]],
                    max_new_tokens: int = 8) -> dict:
    """Base reference, then for each condition: apply the edit, undo it, compare, reset.

    conditions: (name, revoke_mode, svd_q), e.g. ("svd15", "svd", 15). One editor is
    reused across conditions by setting its revoke_mode and svd_q before each undo
    (both are read in RomeEditor.revoke). The edited model (before any undo) is
    compared once, with the first condition. The editor is reset after each condition.
    """
    ref = base_reference(ed, case, max_new_tokens)
    result = {"base": {p: {"type": r["type"], "n_tokens": int(r["c_ids"].shape[1]),
                           "top2_gap": [round(x, 6) for x in top2_gap(r["logp"]).tolist()]}
                       for p, r in ref.items()},
              "conditions": {}}
    for i, (name, mode, q) in enumerate(conditions):
        ed.revoke_mode, ed.svd_q = mode, q
        h = ed.apply(case)
        if i == 0:
            result["conditions"]["edited"] = compare_to_reference(ed, ref)
        ed.revoke(h)
        result["conditions"][name] = compare_to_reference(ed, ref)
        ed.reset()
    return result
