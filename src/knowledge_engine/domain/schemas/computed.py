"""`ComputedVariables` — KB v1.2 §2.1 + v1.3 C-02 (confidence lives here)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReadinessComponentScores:
    """§2.3 breakdown of readiness_score components (max weights per §4.2)."""

    recovery: int = 0  # 0..35
    load: int = 0  # 0..35
    progression: int = 0  # 0..15
    marathon_prep: int = 0  # 0..15
    p3_adjustments: int = 0  # -10..+10


@dataclass
class ComputedVariables:
    """Output of the compute step — never provided by the user.

    v1.3 C-02: `readiness_confidence_score` is computed in this step
    (was in orchestrator step 7 in v1.2) so GF-06 can be enforced at step 4.
    """

    chronic_load_distance: float = 0.0
    acwr_distance: float | None = None
    acwr_reliable: bool = False
    delta_volume_pct: float | None = None
    delta_volume_reliable: bool = False
    delta_long_run_pct: float | None = None
    estimated_internal_load: float | None = None
    estimated_internal_load_notice: str = "aggregated_RPE_estimate"
    target_marathon_pace_min_km: float | None = None
    target_marathon_pace_source: str = "unavailable"
    experience_level: str = "beginner"
    experience_level_source: str = "declared"  # declared | calculated | reconciled
    readiness_score: int = 0
    readiness_confidence_score: int = 100  # v1.3 C-02 — computed at step 2
    readiness_component_scores: ReadinessComponentScores = field(
        default_factory=ReadinessComponentScores
    )
    fatigue_trend: str = "unknown"  # improving | stable | worsening | unknown
    progression_slope_km_per_week: float = 0.0
    zero_volume_week: bool = False
