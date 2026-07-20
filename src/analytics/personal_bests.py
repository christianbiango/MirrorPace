from dataclasses import dataclass
from datetime import datetime

from src.domain.activity import Activity
from src.analytics.weekly_stats import compute_weekly_stats

MIN_DISTANCE_M = 3000


@dataclass
class PersonalBests:
    longest_run_km: float
    longest_run_date: datetime | None
    fastest_pace_s_per_km: float | None  # sur sorties >= 3km
    fastest_pace_date: datetime | None
    best_week_km: float | None
    best_week_start: object | None       # date
    most_elevation_m: float | None
    most_elevation_date: datetime | None


def compute_personal_bests(activities: list[Activity]) -> PersonalBests | None:
    eligible = [
        a for a in activities
        if a.metrics and a.metrics.distance_m and a.metrics.duration_s
    ]

    if not eligible:
        return None

    longest = max(eligible, key=lambda a: a.metrics.distance_m)

    pace_eligible = [a for a in eligible if a.metrics.distance_m >= MIN_DISTANCE_M]
    fastest = (
        min(pace_eligible, key=lambda a: a.metrics.avg_pace_s_per_km)
        if pace_eligible else None
    )

    weekly = compute_weekly_stats(activities)
    best_week = max(weekly, key=lambda w: w.distance_km) if weekly else None

    elev_eligible = [a for a in eligible if a.metrics.elevation_gain_m]
    most_elevation = (
        max(elev_eligible, key=lambda a: a.metrics.elevation_gain_m)
        if elev_eligible else None
    )

    return PersonalBests(
        longest_run_km=longest.metrics.distance_m / 1000,
        longest_run_date=longest.date,
        fastest_pace_s_per_km=fastest.metrics.avg_pace_s_per_km if fastest else None,
        fastest_pace_date=fastest.date if fastest else None,
        best_week_km=best_week.distance_km if best_week else None,
        best_week_start=best_week.week_start if best_week else None,
        most_elevation_m=most_elevation.metrics.elevation_gain_m if most_elevation else None,
        most_elevation_date=most_elevation.date if most_elevation else None,
    )
