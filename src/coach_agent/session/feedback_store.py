"""Persist user feedback linked to coaching decisions.

File: data/memory/feedback.yaml
Append-only, deduplicated by id — same pattern as MemoryStore.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from src.coach_agent.domain.feedback import FeedbackEntry

_DEFAULT_MEMORY_DIR = Path(__file__).resolve().parents[3] / "data" / "memory"


class FeedbackStore:
    def __init__(self, memory_dir: Path | str | None = None) -> None:
        self._dir = Path(memory_dir) if memory_dir else _DEFAULT_MEMORY_DIR
        self._path = self._dir / "feedback.yaml"

    def add(self, entry: FeedbackEntry) -> bool:
        """Append entry. Returns False (no-op) if id already exists."""
        existing = self._load_raw()
        if any(e.get("id") == entry.id for e in existing):
            return False
        existing.append(_to_dict(entry))
        self._save(existing)
        return True

    def get_all(self, runner_id: str) -> list[FeedbackEntry]:
        return [
            _from_dict(e)
            for e in self._load_raw()
            if e.get("runner_id") == runner_id
        ]

    def _load_raw(self) -> list[dict]:
        if not self._path.exists():
            return []
        with self._path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, list) else []

    def _save(self, entries: list[dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as fh:
            yaml.dump(entries, fh, allow_unicode=True, sort_keys=False, default_flow_style=False)


def _to_dict(e: FeedbackEntry) -> dict:
    return {
        "id": e.id,
        "runner_id": e.runner_id,
        "decision_ref": e.decision_ref,
        "session_id": e.session_id,
        "text": e.text,
        "timestamp": e.timestamp,
    }


def _from_dict(d: dict) -> FeedbackEntry:
    return FeedbackEntry(
        id=d["id"],
        runner_id=d["runner_id"],
        decision_ref=d.get("decision_ref"),
        session_id=d.get("session_id", ""),
        text=d["text"],
        timestamp=d["timestamp"],
    )
