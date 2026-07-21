"""Build the objective portion of WeekInput from activity history.

Manual fields (fatigue_score, sleep_quality_score, pain_regions, etc.)
are accepted as optional kwargs and default to neutral values so the
WeekInput is always valid even without subjective data.
"""

from __future__ import annotations

from datetime import date, timedelta

from src.domain.activity import Activity
from src.knowledge_engine.domain.schemas.runner_state import PainRegion, WeekInput

HISTORY_WEEKS = 8


def build_week_input(
    activities: list[Activity],
    reference_date: date | None = None,
    *,
    fatigue_score: int = 3,
    sleep_quality_score: int = 3,
    pain_regions: list[PainRegion] | None = None,
    avg_weekly_RPE: float | None = None,
    session_notes: str = "",
    fatigue_score_history: list[int] | None = None,
) -> WeekInput:
    """Compute objective WeekInput fields from activities.

    The current week is defined as Monday … reference_date (inclusive).
    Previous week = the 7 days before that Monday.
    """
    ref = reference_date or date.today()
    current_week_start = _monday(ref)
    prev_week_start = current_week_start - timedelta(weeks=1)

    current_acts = _week_activities(activities, current_week_start, ref)
    prev_acts = _week_activities(activities, prev_week_start, current_week_start - timedelta(days=1))

    history = _weekly_distance_history(activities, current_week_start, HISTORY_WEEKS)

    return WeekInput(
        weekly_distance_km=_total_km(current_acts),
        previous_week_distance_km=_total_km(prev_acts),
        weekly_duration_min=_total_duration_min(current_acts),
        long_run_km_last_week=_longest_run_km(current_acts),
        fatigue_score=fatigue_score,
        sleep_quality_score=sleep_quality_score,
        days_since_last_run=_days_since_last_run(activities, ref),
        weekly_distance_history=history,
        long_run_km_previous_week=_longest_run_km(prev_acts) or None,
        avg_weekly_RPE=avg_weekly_RPE,
        pain_regions=pain_regions or [],
        session_notes=session_notes,
        fatigue_score_history=fatigue_score_history or [],
    )


# ── helpers ──────────────────────────────────────────────────────────────────

def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _week_activities(activities: list[Activity], start: date, end: date) -> list[Activity]:
    """Activities whose date falls in [start, end] inclusive."""
    result = []
    for a in activities:
        if a.date is None:
            continue
        d = a.date.date() if hasattr(a.date, "date") else a.date
        if start <= d <= end:
            result.append(a)
    return result


def _total_km(acts: list[Activity]) -> float:
    total_m = sum(
        a.metrics.distance_m for a in acts
        if a.metrics and a.metrics.distance_m is not None
    )
    return round(total_m / 1000, 2)


def _total_duration_min(acts: list[Activity]) -> float:
    total_s = sum(
        a.metrics.duration_s for a in acts
        if a.metrics and a.metrics.duration_s is not None
    )
    return round(total_s / 60, 1)


def _longest_run_km(acts: list[Activity]) -> float:
    distances = [
        a.metrics.distance_m / 1000 for a in acts
        if a.metrics and a.metrics.distance_m is not None
    ]
    return round(max(distances), 2) if distances else 0.0


def _days_since_last_run(activities: list[Activity], ref: date) -> int:
    dated = [
        a.date.date() if hasattr(a.date, "date") else a.date
        for a in activities if a.date is not None
    ]
    if not dated:
        return 999
    last = max(dated)
    delta = (ref - last).days
    return max(0, delta)


def _weekly_distance_history(
    activities: list[Activity],
    current_week_start: date,
    n: int,
) -> list[float]:
    """Last n completed weeks, most recent first (excludes current ongoing week)."""
    result = []
    for i in range(1, n + 1):
        week_start = current_week_start - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        acts = _week_activities(activities, week_start, week_end)
        result.append(_total_km(acts))
    return result
