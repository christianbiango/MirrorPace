from dataclasses import dataclass
from datetime import timedelta

from src.domain.activity import Activity

MIN_DISTANCE_M = 3000


@dataclass
class PaceTrend:
    current_pace_s_per_km: float
    previous_pace_s_per_km: float | None
    delta_s: float | None        # négatif = progression (on va plus vite)
    window_weeks: int

    @property
    def is_improving(self) -> bool | None:
        if self.delta_s is None:
            return None
        return self.delta_s < 0


def compute_pace_trend(activities: list[Activity], window_weeks: int = 4) -> PaceTrend | None:
    eligible = sorted(
        [
            a for a in activities
            if a.date
            and a.metrics
            and a.metrics.distance_m
            and a.metrics.distance_m >= MIN_DISTANCE_M
            and a.metrics.duration_s
        ],
        key=lambda a: a.date,
    )

    if not eligible:
        return None

    latest = eligible[-1].date
    cutoff_current = latest - timedelta(weeks=window_weeks)
    cutoff_previous = cutoff_current - timedelta(weeks=window_weeks)

    current = [a for a in eligible if a.date >= cutoff_current]
    previous = [a for a in eligible if cutoff_previous <= a.date < cutoff_current]

    current_pace = _weighted_pace(current)
    if current_pace is None:
        return None

    previous_pace = _weighted_pace(previous)

    return PaceTrend(
        current_pace_s_per_km=current_pace,
        previous_pace_s_per_km=previous_pace,
        delta_s=current_pace - previous_pace if previous_pace is not None else None,
        window_weeks=window_weeks,
    )


def _weighted_pace(activities: list[Activity]) -> float | None:
    """Allure pondérée par la distance (évite que les petites sorties biaisent la moyenne)."""
    total_distance_m = sum(a.metrics.distance_m for a in activities)
    total_duration_s = sum(a.metrics.duration_s for a in activities)
    if total_distance_m == 0:
        return None
    return total_duration_s / (total_distance_m / 1000)
