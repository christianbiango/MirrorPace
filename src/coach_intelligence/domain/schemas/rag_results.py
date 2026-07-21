from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class ScientificSnippet:
    rule_id: str | None
    source: str
    claim: str
    explanation: str
    relevance: float = 0.0


@dataclass
class MemorySnippet:
    type: Literal["pattern", "warning_precedent", "positive_precedent"]
    reference_period: str
    observation: str
    relevance_note: str
    similarity_score: float = 0.0
