"""`RunnerState` and sub-schemas — KB v1.2 §1 + v1.3 §4.1 (fatigue_score_history)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RunnerStateMeta:
    """§1.2 — traceability of input."""

    runner_id: str
    week_start_date: str  # ISO-8601 date (should be Monday)
    submitted_at: str  # ISO-8601 datetime
    schema_version: str = "1.3.1"


@dataclass
class RunnerProfile:
    """§1.3 — collected once, updated occasionally."""

    age: int
    experience_level_declared: str  # {beginner, intermediate, advanced}
    sessions_per_week_available: int
    sex: str = "unspecified"
    pathologies_connues: list[str] = field(default_factory=list)
    recent_race_time_10k: int | None = None  # seconds
    recent_race_time_half: int | None = None  # seconds
    recent_race_time_marathon: int | None = None  # seconds
    VMA_kmh: float | None = None
    race_target_time: int | None = None  # seconds
    race_target_date: str | None = None  # ISO-8601 date
    years_running: float | None = None  # optional (D-04)


@dataclass
class PainRegion:
    """§1.4.1."""

    region: str  # PAIN_REGION_ENUM
    intensity: int  # 0..5
    days_persistent: int
    pain_trend: str = "unknown"  # improving | stable | worsening | unknown
    mechanism: str = "unknown"  # acute | chronic | mechanical | overuse | unknown


@dataclass
class WeekInput:
    """§1.4 + v1.3 C-04 (fatigue_score_history)."""

    weekly_distance_km: float
    previous_week_distance_km: float
    weekly_duration_min: float
    long_run_km_last_week: float
    fatigue_score: int  # 1..5 — 1=faible, 5=extrême
    sleep_quality_score: int  # 1..5 — 1=mauvaise, 5=excellente
    days_since_last_run: int
    weekly_distance_history: list[float] = field(default_factory=list)  # recent → old
    long_run_km_previous_week: float | None = None
    avg_weekly_RPE: float | None = None  # 0..10
    pain_regions: list[PainRegion] = field(default_factory=list)
    session_notes: str = ""
    # v1.3 C-04 — explicit field, recent → old, values ∈ {1..5}
    fatigue_score_history: list[int] = field(default_factory=list)


@dataclass
class PlanContext:
    """§1.5."""

    current_phase: str = "general"  # PHASE_ENUM
    weeks_to_race: int | None = None
    weeks_since_last_injury: int | None = None
    terrain_type: str = "road"
    mood_motivation_score: int | None = None


@dataclass
class RunnerState:
    """§1.1 — top-level input to the engine."""

    meta: RunnerStateMeta
    profile: RunnerProfile
    week: WeekInput
    context: PlanContext


def parse_iso_date(value: str) -> datetime:
    """Parse an ISO-8601 date or datetime string (kept local for testability)."""
    # Accept both 'YYYY-MM-DD' and full datetime forms.
    return datetime.fromisoformat(value)
