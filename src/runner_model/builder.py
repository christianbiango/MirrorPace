from collections import Counter
from datetime import datetime, timedelta, timezone

from src.activity_intelligence.classifier import classify
from src.activity_intelligence.context import AthleteContext
from src.analytics.pace_trends import compute_pace_trend
from src.analytics.personal_bests import compute_personal_bests
from src.analytics.weekly_stats import compute_weekly_stats
from src.domain.activity import Activity
from src.runner_model.snapshot import (
    FitnessWindow,
    FitnessTrend,
    IntensityDistribution,
    RunnerSnapshot,
)

CURRENT_WINDOW_WEEKS = 4


def build_snapshot(activities: list[Activity]) -> RunnerSnapshot:
    now = datetime.now(tz=timezone.utc)

    total_distance_km = sum(
        a.metrics.distance_m for a in activities
        if a.metrics and a.metrics.distance_m
    ) / 1000

    dated = [a for a in activities if a.date]
    active_since = min((a.date.date() for a in dated), default=None)

    ctx = AthleteContext.from_activities(activities)
    pb = compute_personal_bests(activities)
    trend = compute_pace_trend(activities, window_weeks=CURRENT_WINDOW_WEEKS)

    current_window = _build_current_window(activities, now)
    fitness_trend = _build_fitness_trend(trend)
    intensity = _build_intensity(activities, ctx)

    return RunnerSnapshot(
        computed_at=now,
        total_activities=len(activities),
        total_distance_km=round(total_distance_km, 2),
        active_since=active_since,
        fitness_trend=fitness_trend,
        current_window=current_window,
        avg_pace_s_per_km=ctx.avg_pace_s_per_km if ctx else None,
        avg_distance_km=ctx.avg_distance_m / 1000 if ctx else None,
        intensity=intensity,
        longest_run_km=pb.longest_run_km if pb else None,
        fastest_pace_s_per_km=pb.fastest_pace_s_per_km if pb else None,
        best_week_km=pb.best_week_km if pb else None,
    )


def _build_current_window(activities: list[Activity], now: datetime) -> FitnessWindow | None:
    cutoff = now - timedelta(weeks=CURRENT_WINDOW_WEEKS)
    recent = [a for a in activities if a.date and a.date >= cutoff]

    if not recent:
        return None

    weekly = compute_weekly_stats(recent)
    if not weekly:
        return None

    total_km = sum(w.distance_km for w in weekly)
    avg_weekly_km = total_km / CURRENT_WINDOW_WEEKS

    paced = [a for a in recent if a.metrics and a.metrics.avg_pace_s_per_km]
    if not paced:
        return None

    total_duration = sum(a.metrics.duration_s for a in paced)
    total_distance = sum(a.metrics.distance_m for a in paced)
    avg_pace = total_duration / (total_distance / 1000)

    return FitnessWindow(
        avg_weekly_km=round(avg_weekly_km, 2),
        avg_pace_s_per_km=round(avg_pace, 1),
        sessions=len(recent),
    )


def _build_fitness_trend(trend) -> FitnessTrend:
    if trend is None or trend.delta_s is None:
        return "unknown"
    if trend.delta_s < -10:
        return "improving"
    if trend.delta_s > 10:
        return "declining"
    return "stable"


def _build_intensity(activities: list[Activity], ctx: AthleteContext | None) -> IntensityDistribution | None:
    if ctx is None or not activities:
        return None

    classified = [classify(a, ctx) for a in activities]
    total = len(classified)
    counts = Counter(c.intensity for c in classified)

    return IntensityDistribution(
        easy_pct=round(counts["easy"] / total * 100, 1),
        moderate_pct=round(counts["moderate"] / total * 100, 1),
        hard_pct=round(counts["hard"] / total * 100, 1),
        unknown_pct=round(counts["unknown"] / total * 100, 1),
    )
