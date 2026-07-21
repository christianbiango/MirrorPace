"""Unit tests for WeekInputBuilder — objective fields computed from activities."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from src.runner_model.week_input_builder import (
    HISTORY_WEEKS,
    _monday,
    build_week_input,
)
from src.domain.activity import Activity, ActivityMetrics


def _act(d: date, distance_m: float, duration_s: float = 3600.0) -> Activity:
    dt = datetime(d.year, d.month, d.day, 10, 0, tzinfo=timezone.utc)
    metrics = ActivityMetrics(
        distance_m=distance_m,
        duration_s=duration_s,
        elevation_gain_m=None,
    )
    return Activity(
        source_file=None,
        source_type="FIT",
        date=dt,
        sport_type="running",
        metrics=metrics,
        physiology=None,
    )


# Reference Monday for all tests
REF = date(2025, 7, 21)   # Monday


def test_monday_helper():
    assert _monday(REF) == REF
    assert _monday(date(2025, 7, 23)) == REF   # Wednesday → same week
    assert _monday(date(2025, 7, 27)) == REF   # Sunday → same week


def test_current_week_distance():
    # REF is Monday July 21; use a mid-week reference to include multiple days
    acts = [_act(date(2025, 7, 21), 10_000), _act(date(2025, 7, 22), 8_000)]
    week = build_week_input(acts, reference_date=date(2025, 7, 23))  # Wednesday
    assert week.weekly_distance_km == pytest.approx(18.0)


def test_previous_week_distance():
    acts = [_act(date(2025, 7, 14), 12_000)]   # previous Monday
    week = build_week_input(acts, reference_date=REF)
    assert week.previous_week_distance_km == pytest.approx(12.0)


def test_current_week_excludes_previous():
    acts = [
        _act(date(2025, 7, 14), 10_000),  # prev week
        _act(date(2025, 7, 21), 5_000),   # current week
    ]
    week = build_week_input(acts, reference_date=REF)
    assert week.weekly_distance_km == pytest.approx(5.0)
    assert week.previous_week_distance_km == pytest.approx(10.0)


def test_duration_in_minutes():
    acts = [_act(REF, 10_000, duration_s=3600)]
    week = build_week_input(acts, reference_date=REF)
    assert week.weekly_duration_min == pytest.approx(60.0)


def test_long_run_current_week():
    acts = [_act(REF, 5_000), _act(REF, 15_000)]
    week = build_week_input(acts, reference_date=REF)
    assert week.long_run_km_last_week == pytest.approx(15.0)


def test_long_run_previous_week():
    acts = [_act(date(2025, 7, 16), 18_000)]  # Wednesday prev week
    week = build_week_input(acts, reference_date=REF)
    assert week.long_run_km_previous_week == pytest.approx(18.0)


def test_days_since_last_run_today():
    acts = [_act(REF, 10_000)]
    week = build_week_input(acts, reference_date=REF)
    assert week.days_since_last_run == 0


def test_days_since_last_run_gap():
    acts = [_act(date(2025, 7, 18), 10_000)]   # 3 days ago
    week = build_week_input(acts, reference_date=REF)
    assert week.days_since_last_run == 3


def test_days_since_last_run_no_activities():
    week = build_week_input([], reference_date=REF)
    assert week.days_since_last_run == 999


def test_history_length():
    acts = [_act(date(2025, 7, 7), 10_000)]   # 2 weeks ago
    week = build_week_input(acts, reference_date=REF)
    assert len(week.weekly_distance_history) == HISTORY_WEEKS


def test_history_excludes_current_week():
    """Current week activities must NOT appear in history."""
    acts = [_act(REF, 20_000)]   # current week
    week = build_week_input(acts, reference_date=REF)
    # All history entries should be 0 (current week excluded)
    assert all(v == 0.0 for v in week.weekly_distance_history)


def test_history_most_recent_first():
    prev = date(2025, 7, 14)    # 1 week ago
    older = date(2025, 7, 7)    # 2 weeks ago
    acts = [_act(prev, 12_000), _act(older, 8_000)]
    week = build_week_input(acts, reference_date=REF)
    assert week.weekly_distance_history[0] == pytest.approx(12.0)
    assert week.weekly_distance_history[1] == pytest.approx(8.0)


def test_empty_activities_no_crash():
    week = build_week_input([], reference_date=REF)
    assert week.weekly_distance_km == 0.0
    assert week.previous_week_distance_km == 0.0
    assert week.weekly_duration_min == 0.0
    assert week.long_run_km_last_week == 0.0
    assert week.long_run_km_previous_week is None


def test_manual_fields_defaults():
    week = build_week_input([], reference_date=REF)
    assert week.fatigue_score == 3
    assert week.sleep_quality_score == 3
    assert week.pain_regions == []
    assert week.avg_weekly_RPE is None


def test_manual_fields_override():
    from src.knowledge_engine.domain.schemas.runner_state import PainRegion
    pain = [PainRegion(region="knee", intensity=2, days_persistent=3)]
    week = build_week_input(
        [],
        reference_date=REF,
        fatigue_score=5,
        sleep_quality_score=2,
        pain_regions=pain,
        avg_weekly_RPE=7.0,
        session_notes="Hard week",
        fatigue_score_history=[4, 3, 3],
    )
    assert week.fatigue_score == 5
    assert week.sleep_quality_score == 2
    assert week.pain_regions == pain
    assert week.avg_weekly_RPE == 7.0
    assert week.session_notes == "Hard week"
    assert week.fatigue_score_history == [4, 3, 3]
