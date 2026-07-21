from __future__ import annotations

from dataclasses import dataclass, field

from .interpreted_decision import InterpretedDecision
from .personalization import PersonalizationContext
from .rag_results import MemorySnippet, ScientificSnippet


@dataclass
class ReasoningContext:
    interpreted: InterpretedDecision
    personalization: PersonalizationContext
    scientific_snippets: list[ScientificSnippet] = field(default_factory=list)
    memory_snippets: list[MemorySnippet] = field(default_factory=list)
    token_budget_used: int = 0
