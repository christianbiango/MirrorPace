"""Persist and load CoachingDecision and RunnerEvent entries as YAML.

Files:
    data/memory/decisions.yaml
    data/memory/events.yaml

Append-only pattern: new entries are added at the end of the list.
Deduplication is enforced by `id` — adding an existing id is a no-op.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .domain import CoachingDecision, RunnerEvent

_DEFAULT_MEMORY_DIR = Path(__file__).resolve().parents[2] / "data" / "memory"


class MemoryStore:
    def __init__(self, memory_dir: Path | str | None = None) -> None:
        self._dir = Path(memory_dir) if memory_dir else _DEFAULT_MEMORY_DIR
        self._decisions_path = self._dir / "decisions.yaml"
        self._events_path = self._dir / "events.yaml"

    # ── decisions ────────────────────────────────────────────────────────────

    def add_decision(self, decision: CoachingDecision) -> bool:
        """Append decision. Returns False (no-op) if id already exists."""
        existing = self._load_raw(self._decisions_path)
        if any(e.get("id") == decision.id for e in existing):
            return False
        existing.append(_decision_to_dict(decision))
        self._save(self._decisions_path, existing)
        return True

    def get_decisions(self, runner_id: str) -> list[CoachingDecision]:
        return [
            _dict_to_decision(e)
            for e in self._load_raw(self._decisions_path)
            if e.get("runner_id") == runner_id
        ]

    # ── events ────────────────────────────────────────────────────────────────

    def add_event(self, event: RunnerEvent) -> bool:
        """Append event. Returns False (no-op) if id already exists."""
        existing = self._load_raw(self._events_path)
        if any(e.get("id") == event.id for e in existing):
            return False
        existing.append(_event_to_dict(event))
        self._save(self._events_path, existing)
        return True

    def get_events(self, runner_id: str) -> list[RunnerEvent]:
        return [
            _dict_to_event(e)
            for e in self._load_raw(self._events_path)
            if e.get("runner_id") == runner_id
        ]

    # ── internals ─────────────────────────────────────────────────────────────

    def _load_raw(self, path: Path) -> list[dict]:
        if not path.exists():
            return []
        with path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, list) else []

    def _save(self, path: Path, entries: list[dict]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            yaml.dump(entries, fh, allow_unicode=True, sort_keys=False, default_flow_style=False)


# ── serialization ─────────────────────────────────────────────────────────────

def _decision_to_dict(d: CoachingDecision) -> dict:
    return {
        "id": d.id,
        "runner_id": d.runner_id,
        "date": d.date,
        "week_start": d.week_start,
        "decision_ref": d.decision_ref,
        "action": d.action,
        "primary_reason": d.primary_reason,
        "dominant_rules": d.dominant_rules,
        "key_metrics_snapshot": d.key_metrics_snapshot,
        "expected_outcome": d.expected_outcome,
        "actual_outcome": d.actual_outcome,
        "outcome_date": d.outcome_date,
        "text": d.text,
    }


def _dict_to_decision(e: dict) -> CoachingDecision:
    return CoachingDecision(
        id=e["id"],
        runner_id=e["runner_id"],
        date=e["date"],
        week_start=e["week_start"],
        decision_ref=e["decision_ref"],
        action=e["action"],
        primary_reason=e["primary_reason"],
        dominant_rules=e.get("dominant_rules", []),
        key_metrics_snapshot=e.get("key_metrics_snapshot", {}),
        expected_outcome=e.get("expected_outcome", ""),
        actual_outcome=e.get("actual_outcome"),
        outcome_date=e.get("outcome_date"),
        text=e.get("text", ""),
    )


def _event_to_dict(ev: RunnerEvent) -> dict:
    return {
        "id": ev.id,
        "runner_id": ev.runner_id,
        "date": ev.date,
        "event_type": ev.event_type,
        "description": ev.description,
        "body_part": ev.body_part,
        "severity": ev.severity,
        "resolved_date": ev.resolved_date,
        "notes": ev.notes,
        "text": ev.text,
    }


def _dict_to_event(e: dict) -> RunnerEvent:
    return RunnerEvent(
        id=e["id"],
        runner_id=e["runner_id"],
        date=e["date"],
        event_type=e["event_type"],
        description=e["description"],
        body_part=e.get("body_part"),
        severity=e.get("severity"),
        resolved_date=e.get("resolved_date"),
        notes=e.get("notes", ""),
        text=e.get("text", ""),
    )
