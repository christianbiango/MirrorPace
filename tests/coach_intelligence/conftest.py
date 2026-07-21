"""Shared fixtures and stubs for coach_intelligence tests."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone

from src.coach_intelligence.domain.schemas.coach_response import RawLLMResponse
from src.knowledge_engine.api import (
    Decision,
    DecisionEnvelope,
    DecisionMeta,
    LlmContext,
    PlanContext,
    PlanHint,
    ReadinessOut,
    RuleOutcome,
    RunnerProfile,
    RunnerState,
    RunnerStateMeta,
    WeekInput,
)
from src.runner_model.snapshot import (
    FitnessWindow,
    IntensityDistribution,
    RunnerSnapshot,
)

_DEFAULT_LLM_PAYLOAD = {
    "decision_summary": "Réduire le volume cette semaine.",
    "main_message": "Il est recommandé de réduire le volume d'entraînement.",
    "scientific_context": ["Basé sur la recherche de Gabbett (2016)."],
    "personal_context": ["Compte tenu de votre historique récent."],
    "plan_hints_formatted": [],
}


class StubLLMClient:
    def __init__(self, response_text: str | None = None) -> None:
        self.response_text = response_text or json.dumps(_DEFAULT_LLM_PAYLOAD)
        self.calls: list[tuple[str, str]] = []

    def generate(self, system_prompt: str, user_prompt: str) -> RawLLMResponse:
        self.calls.append((system_prompt, user_prompt))
        return RawLLMResponse(
            text=self.response_text,
            model="stub",
            input_tokens=100,
            output_tokens=50,
        )


def make_rule_outcome(
    rule_id: str = "RULE-005",
    priority: str = "P2",
    triggered: bool = True,
    reason: str = "test reason",
    variables_snapshot: dict | None = None,
) -> RuleOutcome:
    return RuleOutcome(
        rule_id=rule_id,
        priority=priority,
        triggered=triggered,
        reason=reason,
        variables_snapshot=variables_snapshot or {},
    )


def make_envelope(
    action: str = "maintain",
    priority: str = "P2",
    medical: bool = False,
    medical_reason: str | None = None,
    confidence: str = "high",
    triggered_rules: list[RuleOutcome] | None = None,
    plan_hints: list[PlanHint] | None = None,
) -> DecisionEnvelope:
    if triggered_rules is None:
        triggered_rules = [make_rule_outcome(priority=priority)]
    return DecisionEnvelope(
        meta=DecisionMeta(
            engine_version="1.0",
            config_hash="abc123",
            computed_at=datetime.now(tz=timezone.utc).isoformat(),
            schema_version="1.3.1",
        ),
        decision=Decision(
            action=action,
            delta_pct=0.0,
            delta_pct_range=(0.0, 0.0),
            absolute_next_week_target_km=50.0,
        ),
        readiness=ReadinessOut(score=70, confidence_score=80),
        triggered_rules=triggered_rules,
        medical_referral=medical,
        medical_referral_reason=medical_reason,
        llm_context=LlmContext(
            reasons_human_readable=["primary reason", "secondary reason"],
            confidence_caveat=confidence,
        ),
        plan_hints=plan_hints or [],
    )


def make_snapshot(
    experience: str = "intermediate",
    total_activities: int = 50,
    fitness_trend: str = "stable",
    active_since: date | None = None,
    years_running: float | None = None,
    with_current_window: bool = True,
    with_intensity: bool = True,
) -> RunnerSnapshot:
    return RunnerSnapshot(
        computed_at=datetime.now(tz=timezone.utc),
        total_activities=total_activities,
        total_distance_km=2500.0,
        active_since=active_since or date(2022, 1, 1),
        fitness_trend=fitness_trend,  # type: ignore[arg-type]
        current_window=FitnessWindow(
            avg_weekly_km=52.0,
            avg_pace_s_per_km=320.0,
            sessions=16,
        ) if with_current_window else None,
        avg_pace_s_per_km=320.0,
        avg_distance_km=10.5,
        intensity=IntensityDistribution(
            easy_pct=80.0,
            moderate_pct=15.0,
            hard_pct=5.0,
            unknown_pct=0.0,
        ) if with_intensity else None,
        longest_run_km=32.0,
        fastest_pace_s_per_km=280.0,
        best_week_km=75.0,
    )


def make_state(
    runner_id: str = "runner-001",
    experience: str = "intermediate",
    weeks_to_race: int | None = None,
    years_running: float | None = None,
    pathologies: list[str] | None = None,
) -> RunnerState:
    from src.knowledge_engine.api import WeekInput
    return RunnerState(
        meta=RunnerStateMeta(
            runner_id=runner_id,
            week_start_date="2026-07-14",
            submitted_at=datetime.now(tz=timezone.utc).isoformat(),
        ),
        profile=RunnerProfile(
            age=32,
            experience_level_declared=experience,
            sessions_per_week_available=4,
            years_running=years_running,
            pathologies_connues=pathologies or [],
        ),
        week=WeekInput(
            weekly_distance_km=50.0,
            previous_week_distance_km=48.0,
            weekly_duration_min=300.0,
            long_run_km_last_week=18.0,
            fatigue_score=2,
            sleep_quality_score=4,
            days_since_last_run=1,
        ),
        context=PlanContext(weeks_to_race=weeks_to_race),
    )
