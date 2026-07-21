from __future__ import annotations

import re
from typing import Protocol, runtime_checkable


@runtime_checkable
class VectorStore(Protocol):
    def query(self, text: str, k: int) -> list[tuple[str, float, dict]]:
        """Return list of (doc_id, score, doc_metadata) sorted by score desc."""
        ...

    def add(self, documents: list[dict]) -> None:
        """Add documents. Each doc must have 'id' and 'text' keys."""
        ...


class InMemoryVectorStore:
    """Keyword-based Jaccard similarity store — swappable with an embedding store."""

    def __init__(self) -> None:
        self._docs: list[dict] = []

    def add(self, documents: list[dict]) -> None:
        self._docs.extend(documents)

    def query(self, text: str, k: int) -> list[tuple[str, float, dict]]:
        query_tokens = set(_tokenize(text))
        if not query_tokens:
            return []

        scored: list[tuple[str, float, dict]] = []
        for doc in self._docs:
            doc_text = doc.get("text", "") + " " + " ".join(
                str(t) for t in doc.get("tags", [])
            )
            doc_tokens = set(_tokenize(doc_text))
            if not doc_tokens:
                continue
            intersection = len(query_tokens & doc_tokens)
            union = len(query_tokens | doc_tokens)
            score = intersection / union if union else 0.0
            if score > 0.0:
                scored.append((doc["id"], score, doc))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    def __len__(self) -> int:
        return len(self._docs)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())
