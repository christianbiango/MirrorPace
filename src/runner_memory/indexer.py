"""Build a VectorStore from runner memory entries for use by RunnerContextRetriever."""

from __future__ import annotations

from src.coach_intelligence.rag.store import InMemoryVectorStore

from .domain import CoachingDecision, RunnerEvent
from .store import MemoryStore


def build_runner_context_store(runner_id: str, memory_store: MemoryStore) -> InMemoryVectorStore:
    """Load all memory entries for a runner and index them for Jaccard retrieval."""
    store = InMemoryVectorStore()

    decisions = memory_store.get_decisions(runner_id)
    events = memory_store.get_events(runner_id)

    docs = [_decision_to_doc(d) for d in decisions] + [_event_to_doc(e) for e in events]
    if docs:
        store.add(docs)

    return store


def _decision_to_doc(d: CoachingDecision) -> dict:
    metrics = d.key_metrics_snapshot
    outcome_part = f" Résultat: {d.actual_outcome}." if d.actual_outcome else ""
    observation = (
        f"Semaine {d.week_start} — {metrics.get('weekly_distance_km', '?'):.1f} km, "
        f"readiness {metrics.get('readiness_score', '?')}/100. "
        f"Décision: {d.action}. {d.primary_reason}.{outcome_part}"
    )
    return {
        "id": f"decision_{d.id}",
        "runner_id": d.runner_id,
        "type": "coaching_decision",
        "reference_period": d.week_start,
        "text": d.text,
        "observation": observation,
        "relevance_note": f"Décision passée : {d.action} (réf. {d.decision_ref})",
    }


def _event_to_doc(e: RunnerEvent) -> dict:
    body = f" ({e.body_part})" if e.body_part else ""
    severity = f" — {e.severity}" if e.severity else ""
    resolved = f" Résolution: {e.resolved_date}." if e.resolved_date else " Non résolu."
    observation = f"{e.event_type.replace('_', ' ').capitalize()}{body}{severity} : {e.description}.{resolved}"
    text = (
        f"{e.event_type} {e.body_part or ''} {e.severity or ''} "
        f"{e.description} {e.date} blessure douleur arrêt"
    )
    return {
        "id": f"event_{e.id}",
        "runner_id": e.runner_id,
        "type": "runner_event",
        "reference_period": e.date,
        "text": text,
        "observation": observation,
        "relevance_note": f"Événement coureur : {e.event_type}",
    }
