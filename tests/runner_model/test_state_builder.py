"""Unit tests for RunnerStateBuilder."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from src.knowledge_engine.domain.schemas.runner_state import PlanContext, RunnerProfile
from src.runner_model.state_builder import _monday_iso, build_runner_state


def _profile(**kw) -> RunnerProfile:
    defaults = dict(age=30, experience_level_declared="intermediate", sessions_per_week_available=4)
    defaults.update(kw)
    return RunnerProfile(**defaults)


REF = date(2025, 7, 21)


def test_meta_runner_id():
    state = build_runner_state([], _profile(), runner_id="athlete-1", reference_date=REF)
    assert state.meta.runner_id == "athlete-1"


def test_meta_week_start_is_monday():
    state = build_runner_state([], _profile(), reference_date=date(2025, 7, 23))  # Wednesday
    assert state.meta.week_start_date == "2025-07-21"


def test_meta_submitted_at_is_iso():
    state = build_runner_state([], _profile(), reference_date=REF)
    # Should parse without error
    datetime.fromisoformat(state.meta.submitted_at)


def test_profile_preserved():
    profile = _profile(age=28, experience_level_declared="advanced")
    state = build_runner_state([], profile, reference_date=REF)
    assert state.profile.age == 28
    assert state.profile.experience_level_declared == "advanced"


def test_default_plan_context():
    state = build_runner_state([], _profile(), reference_date=REF)
    assert state.context.current_phase == "general"
    assert state.context.weeks_to_race is None


def test_custom_plan_context():
    ctx = PlanContext(weeks_to_race=8, current_phase="specific")
    state = build_runner_state([], _profile(), plan_context=ctx, reference_date=REF)
    assert state.context.weeks_to_race == 8
    assert state.context.current_phase == "specific"


def test_week_input_objective_fields_wired():
    from src.domain.activity import Activity, ActivityMetrics
    dt = datetime(2025, 7, 21, 10, 0, tzinfo=timezone.utc)
    act = Activity(
        source_file=None,
        source_type="FIT",
        date=dt,
        sport_type="running",
        metrics=ActivityMetrics(distance_m=10_000, duration_s=3600, elevation_gain_m=None),
        physiology=None,
    )
    state = build_runner_state([act], _profile(), reference_date=REF)
    assert state.week.weekly_distance_km == pytest.approx(10.0)
    assert state.week.weekly_duration_min == pytest.approx(60.0)


def test_manual_fields_forwarded():
    state = build_runner_state(
        [], _profile(),
        reference_date=REF,
        fatigue_score=5,
        sleep_quality_score=1,
    )
    assert state.week.fatigue_score == 5
    assert state.week.sleep_quality_score == 1


def test_monday_iso():
    assert _monday_iso(date(2025, 7, 21)) == "2025-07-21"
    assert _monday_iso(date(2025, 7, 23)) == "2025-07-21"   # Wednesday → Monday
    assert _monday_iso(date(2025, 7, 27)) == "2025-07-21"   # Sunday → Monday
