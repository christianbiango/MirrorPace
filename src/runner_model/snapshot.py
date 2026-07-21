from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

FitnessTrend = Literal["improving", "stable", "declining", "unknown"]


@dataclass
class FitnessWindow:
    avg_weekly_km: float
    avg_pace_s_per_km: float
    sessions: int


@dataclass
class IntensityDistribution:
    easy_pct: float
    moderate_pct: float
    hard_pct: float
    unknown_pct: float


@dataclass
class RunnerSnapshot:
    computed_at: datetime

    # Career
    total_activities: int
    total_distance_km: float
    active_since: date | None

    # Current state
    fitness_trend: FitnessTrend
    current_window: FitnessWindow | None

    # Training profile
    avg_pace_s_per_km: float | None
    avg_distance_km: float | None
    intensity: IntensityDistribution | None

    # Personal bests
    longest_run_km: float | None
    fastest_pace_s_per_km: float | None
    best_week_km: float | None
