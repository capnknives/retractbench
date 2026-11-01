"""Core data types. Pure Python: no torch import here."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Protocol


@dataclass
class EditCase:
    """One fact to write, probe and revoke.

    - `paraphrases`: reworded versions of `prompt`; the edit *should* apply.
    - `unrelated`: easy negatives, different kind of question; must not change.
    - `hard_negatives`: same kind of question about a different subject
      ("The capital of Japan is" for an edit about Velmora's capital).
      Must not change, and much harder to protect than `unrelated`.
    - `subject`: the entity the fact is about, as it appears in `prompt`.
      Needed by editors that key on the subject token.

    Use fictional facts where possible, so "revoked" has a clean meaning:
    the model goes back to not knowing, rather than back to a real-world answer.
    """

    id: str
    prompt: str
    target: str
    paraphrases: list[str] = field(default_factory=list)
    unrelated: list[str] = field(default_factory=list)
    hard_negatives: list[str] = field(default_factory=list)
    subject: str | None = None

    @classmethod
    def from_dict(cls, d: dict) -> "EditCase":
        return cls(
            id=str(d["id"]),
            prompt=d["prompt"],
            target=d["target"],
            paraphrases=list(d.get("paraphrases", [])),
            unrelated=list(d.get("unrelated", [])),
            hard_negatives=list(d.get("hard_negatives", [])),
            subject=d.get("subject"),
        )


@dataclass
class CaseResult:
    case_id: str
    edit_success: bool
    edit_success_loose: bool
    paraphrase_generalization: float
    locality: float
    locality_hard: float
    revocation_exact: bool
    target_leak_after_revoke: float
    apply_ms: float
    revoke_ms: float
    outputs: dict[str, dict[str, str]]

    def to_dict(self) -> dict:
        return asdict(self)


class Editor(Protocol):
    """Anything that can write, revoke and generate. GRACE, WISE, LoRA and
    RAG baselines all implement this same interface."""

    name: str

    def generate(self, prompt: str, max_new_tokens: int = 8) -> str: ...

    def apply(self, case: EditCase) -> Any:
        """Write the edit; return a handle that `revoke` accepts."""
        ...

    def revoke(self, handle: Any) -> None: ...

    def config(self) -> dict: ...
