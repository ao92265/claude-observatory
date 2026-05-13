"""Shared types."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Suggestion:
    id: str
    kind: str
    target: str
    rationale: str
    diff: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    estimated_savings_usd_month: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
