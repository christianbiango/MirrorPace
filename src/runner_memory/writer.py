"""Build a CoachingDecision from a DecisionEnvelope and persist it.

Called between Knowledge Engine output and Coach Intelligence input:

    envelope = run_engine(state, config)
    MemoryWriter(store).record(envelope, state)   ← here
    response  = build_coach_response(envelope, ...)
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone

from src.knowledge_engine.api import DecisionEnvelope, RunnerState

from .domain import CoachingDecision
from .store import MemoryStore

_EXPECTED_OUTCOMES: dict[str, str] = {
    "slight_increase": "augmentation progressive de la charge",
    "significant_increase": "forte augmentation de la charge",
    "maintain": "maintien du volume actuel",
    "reduce_volume": "réduction du volume pour récupération",
    "deload": "semaine de décharge complète",
    "rest": "repos complet",
    "emergency_stop": "arrêt d'urgence — référence médicale",
}


class MemoryWriter:
    def __init__(self, store: MemoryStore | None = None) -> None:
        self._store = store or MemoryStore()

    def record(self, envelope: DecisionEnvelope, state: RunnerState) -> CoachingDecision:
        """Create a CoachingDecision from the envelope and persist it."""
        runner_id = state.meta.runner_id
        week_start = state.meta.week_start_date
        action = envelope.decision.action
        today = datetime.now(tz=timezone.utc).date().isoformat()

        entry_id = _hash(f"{runner_id}:{week_start}:{action}")
        decision_ref = _hash(
            f"{envelope.meta.computed_at}:{action}:{envelope.readiness.score}"
        )

        triggered = [r for r in envelope.triggered_rules if r.triggered]
        dominant_rules = [r.rule_id for r in triggered]
        primary_reason = triggered[0].reason if triggered else action

        metrics = _build_metrics_snapshot(envelope, state)
        text = _build_text(week_start, action, dominant_rules, metrics, primary_reason)

        decision = CoachingDecision(
            id=entry_id,
            runner_id=runner_id,
            date=today,
            week_start=week_start,
            decision_ref=decision_ref,
            action=action,
            primary_reason=primary_reason,
            dominant_rules=dominant_rules,
            key_metrics_snapshot=metrics,
            expected_outcome=_EXPECTED_OUTCOMES.get(action, action),
            text=text,
        )

        self._store.add_decision(decision)
        return decision


def _build_metrics_snapshot(envelope: DecisionEnvelope, state: RunnerState) -> dict:
    w = state.week
    metrics: dict = {
        "weekly_distance_km": w.weekly_distance_km,
        "previous_week_distance_km": w.previous_week_distance_km,
        "readiness_score": envelope.readiness.score,
        "readiness_confidence": envelope.readiness.confidence_score,
        "fatigue_score": w.fatigue_score,
        "sleep_quality_score": w.sleep_quality_score,
        "days_since_last_run": w.days_since_last_run,
        "target_next_week_km": round(envelope.decision.absolute_next_week_target_km, 1),
    }
    # Include ACWR if present in any triggered rule's variables snapshot
    for rule in envelope.triggered_rules:
        if rule.triggered and isinstance(rule.variables_snapshot, dict):
            acwr = rule.variables_snapshot.get("acwr_distance")
            if acwr is not None:
                metrics["acwr"] = round(float(acwr), 2)
                break
    return metrics


def _build_text(
    week_start: str,
    action: str,
    dominant_rules: list[str],
    metrics: dict,
    primary_reason: str,
) -> str:
    vol = metrics.get("weekly_distance_km", 0)
    readiness = metrics.get("readiness_score", "?")
    fatigue = metrics.get("fatigue_score", "?")
    rules_str = " ".join(dominant_rules)
    acwr_part = f" ACWR {metrics['acwr']:.2f}" if "acwr" in metrics else ""
    return (
        f"Semaine {week_start} : {vol:.1f}km readiness {readiness}/100"
        f" fatigue {fatigue}/5{acwr_part}."
        f" Décision: {action}. Raison: {primary_reason}. Règles: {rules_str}."
    )


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:12]
