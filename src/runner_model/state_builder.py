"""Build a complete RunnerState from activities + profile + optional manual input.

Single read pattern: caller reads activities once and passes the same list
to both build_snapshot() and build_runner_state() to guarantee temporal
consistency between RunnerSnapshot and RunnerState.week.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from src.domain.activity import Activity
from src.knowledge_engine.domain.schemas.runner_state import (
    PainRegion,
    PlanContext,
    RunnerProfile,
    RunnerState,
    RunnerStateMeta,
    WeekInput,
)
from src.runner_model.week_input_builder import build_week_input


def build_runner_state(
    activities: list[Activity],
    profile: RunnerProfile,
    runner_id: str = "default",
    *,
    plan_context: PlanContext | None = None,
    reference_date: date | None = None,
    # manual weekly subjective inputs
    fatigue_score: int = 3,
    sleep_quality_score: int = 3,
    pain_regions: list[PainRegion] | None = None,
    avg_weekly_RPE: float | None = None,
    session_notes: str = "",
    fatigue_score_history: list[int] | None = None,
) -> RunnerState:
    """Build RunnerState from DB activities and a RunnerProfile.

    Manual fields (fatigue, sleep, pain) default to neutral values so the
    pipeline runs without subjective input.  Callers that collect subjective
    data should pass them explicitly.
    """
    ref = reference_date or date.today()
    week_input = build_week_input(
        activities,
        ref,
        fatigue_score=fatigue_score,
        sleep_quality_score=sleep_quality_score,
        pain_regions=pain_regions,
        avg_weekly_RPE=avg_weekly_RPE,
        session_notes=session_notes,
        fatigue_score_history=fatigue_score_history,
    )

    meta = RunnerStateMeta(
        runner_id=runner_id,
        week_start_date=_monday_iso(ref),
        submitted_at=datetime.now(tz=timezone.utc).isoformat(),
    )

    return RunnerState(
        meta=meta,
        profile=profile,
        week=week_input,
        context=plan_context or PlanContext(),
    )


def _monday_iso(d: date) -> str:
    from datetime import timedelta
    monday = d - timedelta(days=d.weekday())
    return monday.isoformat()
