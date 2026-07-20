from dataclasses import dataclass
from datetime import date, datetime, timedelta
from collections import defaultdict

from src.domain.activity import Activity


@dataclass
class WeekStats:
    week_start: date
    sessions: int
    distance_km: float
    duration_s: float
    elevation_m: float | None
    avg_pace_s_per_km: float | None


def compute_weekly_stats(activities: list[Activity]) -> list[WeekStats]:
    buckets: dict[date, list[Activity]] = defaultdict(list)

    for activity in activities:
        if activity.date and activity.metrics and activity.metrics.distance_m:
            buckets[_week_start(activity.date)].append(activity)

    result = []
    for week, acts in sorted(buckets.items()):
        total_distance_m = sum(
            a.metrics.distance_m for a in acts if a.metrics and a.metrics.distance_m
        )
        total_duration_s = sum(
            a.metrics.duration_s for a in acts if a.metrics and a.metrics.duration_s
        )
        elevations = [
            a.metrics.elevation_gain_m
            for a in acts
            if a.metrics and a.metrics.elevation_gain_m
        ]

        result.append(WeekStats(
            week_start=week,
            sessions=len(acts),
            distance_km=total_distance_m / 1000,
            duration_s=total_duration_s,
            elevation_m=sum(elevations) if elevations else None,
            avg_pace_s_per_km=(
                total_duration_s / (total_distance_m / 1000)
                if total_distance_m > 0 and total_duration_s > 0
                else None
            ),
        ))

    return result


def _week_start(dt: datetime) -> date:
    return (dt.date() - timedelta(days=dt.weekday()))
