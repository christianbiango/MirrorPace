from __future__ import annotations

from ..store import InMemoryVectorStore, VectorStore
from ...domain.schemas.interpreted_decision import InterpretedDecision
from ...domain.schemas.rag_results import ScientificSnippet
from .knowledge_base import SCIENTIFIC_ENTRIES

_DEFAULT_K = 4
_DEFAULT_STORE: InMemoryVectorStore | None = None


def _get_default_store() -> InMemoryVectorStore:
    global _DEFAULT_STORE
    if _DEFAULT_STORE is None:
        _DEFAULT_STORE = _build_default_store()
    return _DEFAULT_STORE


class ScientificRetriever:
    def __init__(self, store: VectorStore | None = None) -> None:
        self._store: VectorStore = store if store is not None else _get_default_store()

    def retrieve(
        self,
        interpreted: InterpretedDecision,
        user_question: str | None = None,
        k: int = _DEFAULT_K,
    ) -> list[ScientificSnippet]:
        query_parts: list[str] = [
            interpreted.action,
            interpreted.primary_reason,
            *interpreted.dominant_rule_ids,
        ]
        if "acwr" in interpreted.key_metrics:
            query_parts.append(f"acwr {interpreted.key_metrics['acwr']}")
        if interpreted.medical_flag and interpreted.medical_reason:
            query_parts.append(interpreted.medical_reason)
        if user_question:
            query_parts.append(user_question)

        query = " ".join(str(p) for p in query_parts if p)
        results = self._store.query(query, k=k)

        snippets: list[ScientificSnippet] = []
        for _doc_id, score, doc in results:
            tags: list[str] = doc.get("tags", [])
            rule_id = next((t for t in tags if t.startswith("RULE-")), None)
            snippets.append(
                ScientificSnippet(
                    rule_id=rule_id,
                    source=doc["source"],
                    claim=doc["claim"],
                    explanation=doc["explanation"],
                    relevance=score,
                )
            )
        return snippets


def _build_default_store() -> InMemoryVectorStore:
    store = InMemoryVectorStore()
    docs = [
        {
            "id": entry["id"],
            "text": " ".join([entry["source"], entry["claim"], entry["explanation"]]),
            "tags": entry["tags"],
            **entry,
        }
        for entry in SCIENTIFIC_ENTRIES
    ]
    store.add(docs)
    return store
