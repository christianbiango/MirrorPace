from __future__ import annotations

from ..store import InMemoryVectorStore, VectorStore
from ...domain.schemas.interpreted_decision import InterpretedDecision
from ...domain.schemas.rag_results import MemorySnippet

_DEFAULT_K = 3


class RunnerContextRetriever:
    def __init__(self, store: VectorStore | None = None) -> None:
        self._store: VectorStore | None = store

    def retrieve(
        self,
        runner_id: str,
        interpreted: InterpretedDecision,
        k: int = _DEFAULT_K,
    ) -> list[MemorySnippet]:
        if self._store is None:
            return []

        query_parts: list[str] = [
            interpreted.action,
            interpreted.severity,
            interpreted.primary_reason,
            *interpreted.dominant_rule_ids,
        ]
        if interpreted.medical_flag:
            query_parts.append("blessure douleur")

        query = " ".join(str(p) for p in query_parts if p)
        results = self._store.query(query, k=k)

        snippets: list[MemorySnippet] = []
        for _doc_id, score, doc in results:
            if doc.get("runner_id") and doc["runner_id"] != runner_id:
                continue
            snippets.append(
                MemorySnippet(
                    type=doc.get("type", "pattern"),
                    reference_period=doc.get("reference_period", ""),
                    observation=doc.get("observation", ""),
                    relevance_note=doc.get("relevance_note", ""),
                    similarity_score=score,
                )
            )
        return snippets
