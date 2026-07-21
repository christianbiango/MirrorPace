"""Test fixture builders — construct RunnerState variants concisely."""

from __future__ import annotations

from dataclasses import replace

from src.knowledge_engine.api import (
    PainRegion,
    PlanContext,
    RunnerProfile,
    RunnerState,
    RunnerStateMeta,
    WeekInput,
)


def make_meta(
    runner_id: str = "runner-uuid",
    week_start_date: str = "2026-07-13",  # Monday
    submitted_at: str = "2026-07-14T09:00:00+00:00",
) -> RunnerStateMeta:
    return RunnerStateMeta(
        runner_id=runner_id,
        week_start_date=week_start_date,
        submitted_at=submitted_at,
    )


def make_profile(
    age: int = 32,
    experience_level_declared: str = "intermediate",
    sessions_per_week_available: int = 4,
    pathologies_connues: list[str] | None = None,
    recent_race_time_10k: int | None = None,
    recent_race_time_half: int | None = 5700,  # 1h35 default
    VMA_kmh: float | None = 16.0,
    race_target_time: int | None = None,
    race_target_date: str | None = None,
    years_running: float | None = None,
) -> RunnerProfile:
    return RunnerProfile(
        age=age,
        experience_level_declared=experience_level_declared,
        sessions_per_week_available=sessions_per_week_available,
        pathologies_connues=pathologies_connues or [],
        recent_race_time_10k=recent_race_time_10k,
        recent_race_time_half=recent_race_time_half,
        VMA_kmh=VMA_kmh,
        race_target_time=race_target_time,
        race_target_date=race_target_date,
        years_running=years_running,
    )


def make_week(
    weekly_distance_km: float = 45.0,
    previous_week_distance_km: float = 42.0,
    weekly_distance_history: list[float] | None = None,
    weekly_duration_min: float = 240.0,
    long_run_km_last_week: float = 18.0,
    long_run_km_previous_week: float | None = 16.0,
    avg_weekly_RPE: float | None = 5.0,
    fatigue_score: int = 2,
    sleep_quality_score: int = 4,
    pain_regions: list[PainRegion] | None = None,
    days_since_last_run: int = 0,
    session_notes: str = "",
    fatigue_score_history: list[int] | None = None,
) -> WeekInput:
    return WeekInput(
        weekly_distance_km=weekly_distance_km,
        previous_week_distance_km=previous_week_distance_km,
        weekly_duration_min=weekly_duration_min,
        long_run_km_last_week=long_run_km_last_week,
        fatigue_score=fatigue_score,
        sleep_quality_score=sleep_quality_score,
        days_since_last_run=days_since_last_run,
        weekly_distance_history=list(
            weekly_distance_history or [42, 40, 38, 36]
        ),
        long_run_km_previous_week=long_run_km_previous_week,
        avg_weekly_RPE=avg_weekly_RPE,
        pain_regions=list(pain_regions or []),
        session_notes=session_notes,
        fatigue_score_history=list(fatigue_score_history or []),
    )


def make_context(
    current_phase: str = "general",
    weeks_to_race: int | None = 20,
    weeks_since_last_injury: int | None = None,
    terrain_type: str = "road",
    mood_motivation_score: int | None = None,
) -> PlanContext:
    return PlanContext(
        current_phase=current_phase,
        weeks_to_race=weeks_to_race,
        weeks_since_last_injury=weeks_since_last_injury,
        terrain_type=terrain_type,
        mood_motivation_score=mood_motivation_score,
    )


def make_state(
    meta: RunnerStateMeta | None = None,
    profile: RunnerProfile | None = None,
    week: WeekInput | None = None,
    context: PlanContext | None = None,
) -> RunnerState:
    return RunnerState(
        meta=meta or make_meta(),
        profile=profile or make_profile(),
        week=week or make_week(),
        context=context or make_context(),
    )


def with_week(state: RunnerState, **fields) -> RunnerState:
    """Return a copy of `state` with the given WeekInput fields overridden."""
    return replace(state, week=replace(state.week, **fields))


def with_profile(state: RunnerState, **fields) -> RunnerState:
    return replace(state, profile=replace(state.profile, **fields))


def with_context(state: RunnerState, **fields) -> RunnerState:
    return replace(state, context=replace(state.context, **fields))
