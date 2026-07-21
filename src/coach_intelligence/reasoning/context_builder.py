from __future__ import annotations

from ..domain.schemas.interpreted_decision import InterpretedDecision
from ..domain.schemas.personalization import PersonalizationContext
from ..domain.schemas.rag_results import MemorySnippet, ScientificSnippet
from ..domain.schemas.reasoning_context import ReasoningContext

_MAX_SCIENTIFIC = 4
_MAX_MEMORY = 3
_CHARS_PER_TOKEN = 4


class ReasoningContextBuilder:
    def __init__(
        self,
        max_scientific: int = _MAX_SCIENTIFIC,
        max_memory: int = _MAX_MEMORY,
    ) -> None:
        self.max_scientific = max_scientific
        self.max_memory = max_memory

    def build(
        self,
        interpreted: InterpretedDecision,
        personalization: PersonalizationContext,
        scientific_snippets: list[ScientificSnippet],
        memory_snippets: list[MemorySnippet],
    ) -> ReasoningContext:
        # Sort by relevance, deduplicate by source, cap
        sorted_sci = sorted(scientific_snippets, key=lambda s: s.relevance, reverse=True)
        seen_sources: set[str] = set()
        deduped_sci: list[ScientificSnippet] = []
        for s in sorted_sci:
            if s.source not in seen_sources:
                deduped_sci.append(s)
                seen_sources.add(s.source)
            if len(deduped_sci) >= self.max_scientific:
                break

        top_memory = sorted(memory_snippets, key=lambda m: m.similarity_score, reverse=True)[
            : self.max_memory
        ]

        token_budget = self._estimate_tokens(interpreted, personalization, deduped_sci, top_memory)

        return ReasoningContext(
            interpreted=interpreted,
            personalization=personalization,
            scientific_snippets=deduped_sci,
            memory_snippets=top_memory,
            token_budget_used=token_budget,
        )

    def _estimate_tokens(self, *args: object) -> int:
        return sum(len(str(a)) for a in args) // _CHARS_PER_TOKEN
