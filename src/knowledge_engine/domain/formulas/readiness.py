"""Readiness score & confidence — KB v1.2 §2.3, §2.4 + v1.3 C-02.

`readiness_confidence_score` is computed here (was moved to ComputedVariables
step in v1.3 so GF-06 can apply during aggregation).
"""

from __future__ import annotations

from datetime import date
from typing import Any

from ..schemas.computed import ReadinessComponentScores
from ..schemas.runner_state import PainRegion, RunnerState


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


# --------------------------------------------------------------------------- #
# Recovery (0..35)
# --------------------------------------------------------------------------- #

def _fatigue_component(fatigue_score: int) -> int:
    """0..15 — 15 if fatigue==1, 0 if fatigue==5, linear."""
    if fatigue_score <= 1:
        return 15
    if fatigue_score >= 5:
        return 0
    return int(round(15 * (5 - fatigue_score) / 4))


def _sleep_component(sleep_score: int) -> int:
    """0..10 — 10 if sleep==5, 0 if sleep==1, linear (v1.2 inverted scale)."""
    if sleep_score <= 1:
        return 0
    if sleep_score >= 5:
        return 10
    return int(round(10 * (sleep_score - 1) / 4))


def _pain_component(pain_regions: list[PainRegion]) -> int:
    """0..10 — 10 - 2 * max_pain_intensity, clamped [0..10]."""
    if not pain_regions:
        return 10
    max_intensity = max((p.intensity for p in pain_regions), default=0)
    return int(_clamp(10 - 2 * max_intensity, 0, 10))


def _recovery_component(week: Any) -> int:
    return (
        _fatigue_component(week.fatigue_score)
        + _sleep_component(week.sleep_quality_score)
        + _pain_component(week.pain_regions)
    )


# --------------------------------------------------------------------------- #
# Load (0..35)
# --------------------------------------------------------------------------- #

def _acwr_component(
    acwr: float | None,
    reliable: bool,
    params: dict[str, Any],
) -> int:
    """0..20 — bell curve centered on [sweet_spot_min..sweet_spot_max]."""
    if acwr is None or not reliable:
        return 0
    lo = params["acwr_sweet_spot_min"]
    hi = params["acwr_sweet_spot_max"]
    if lo <= acwr <= hi:
        return 20
    # Linear decay outside the sweet-spot, zero at ±0.5 from bounds.
    dist = min(abs(acwr - lo), abs(acwr - hi))
    return int(_clamp(20 * (1 - dist / 0.5), 0, 20))


def _delta_volume_component(delta_pct: float | None) -> int:
    """0..10 — 10 if delta<=0, 0 if delta>=15%, linear decrease."""
    if delta_pct is None:
        return 5  # neutral when unknown
    if delta_pct <= 0:
        return 10
    if delta_pct >= 15:
        return 0
    return int(round(10 * (1 - delta_pct / 15)))


def _chronic_baseline_component(
    chronic_load: float,
    phase: str,
    params: dict[str, Any],
) -> int:
    """0..5 — bonus if chronic load covers the current phase (§2.3 [PROD])."""
    if phase == "specific_marathon" and chronic_load >= 40:
        return 5
    if phase == "general" and chronic_load >= 25:
        return 3
    if phase == "taper" and chronic_load >= 30:
        return 4
    return 0


def _load_component(
    computed: Any,
    context: Any,
    params: dict[str, Any],
) -> int:
    return (
        _acwr_component(computed.acwr_distance, computed.acwr_reliable, params)
        + _delta_volume_component(computed.delta_volume_pct)
        + _chronic_baseline_component(
            computed.chronic_load_distance, context.current_phase, params
        )
    )


# --------------------------------------------------------------------------- #
# Progression (0..15)
# --------------------------------------------------------------------------- #

def _slope_component(slope_km_per_week: float) -> int:
    """0..10 — positive controlled slope: full, negative: 0, cap +2 km/wk = 10."""
    if slope_km_per_week <= 0:
        return 5  # neutral (some regression tolerated)
    return int(_clamp(round(5 + slope_km_per_week * 2.5), 0, 10))


def _long_run_component(delta_long_run_pct: float | None, phase: str) -> int:
    """0..5 — depends on progression of long run and current phase."""
    if delta_long_run_pct is None:
        return 2
    if phase == "taper":
        # In taper, decreasing long run is expected.
        if delta_long_run_pct <= 0:
            return 5
        return 1
    if 0 <= delta_long_run_pct <= 10:
        return 5
    if delta_long_run_pct < 0:
        return 3
    return 1  # too aggressive (>10%)


def _progression_component(computed: Any, context: Any) -> int:
    return _slope_component(computed.progression_slope_km_per_week) + _long_run_component(
        computed.delta_long_run_pct, context.current_phase
    )


# --------------------------------------------------------------------------- #
# Marathon prep (0..15)
# --------------------------------------------------------------------------- #

def _phase_coherence_component(phase: str, weeks_to_race: int | None) -> int:
    """0..8 — coherence of current_phase vs weeks_to_race."""
    if weeks_to_race is None:
        return 4
    if phase == "taper" and 0 <= weeks_to_race <= 3:
        return 8
    if phase == "specific_marathon" and 4 <= weeks_to_race <= 12:
        return 8
    if phase == "general" and weeks_to_race >= 12:
        return 8
    if phase == "return_from_injury":
        return 3
    if phase == "off_season":
        return 4
    return 4


def _pace_readiness_component(computed: Any) -> int:
    """0..7 — target_marathon_pace defined AND coherent source."""
    if computed.target_marathon_pace_min_km is None:
        return 0
    if computed.target_marathon_pace_source == "race_target_time":
        return 7
    if computed.target_marathon_pace_source in ("riegel_from_half",):
        return 6
    if computed.target_marathon_pace_source == "riegel_from_10k":
        return 4
    if computed.target_marathon_pace_source == "vma_only":
        return 2
    return 0


def _marathon_prep_component(computed: Any, context: Any) -> int:
    return _phase_coherence_component(
        context.current_phase, context.weeks_to_race
    ) + _pace_readiness_component(computed)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def compute_component_scores(
    state: RunnerState,
    computed: Any,
    params: dict[str, Any],
) -> ReadinessComponentScores:
    return ReadinessComponentScores(
        recovery=_recovery_component(state.week),
        load=_load_component(computed, state.context, params),
        progression=_progression_component(computed, state.context),
        marathon_prep=_marathon_prep_component(computed, state.context),
        p3_adjustments=0,
    )


def compose_readiness_score(components: ReadinessComponentScores) -> int:
    """§2.3 — sum + clamp. P3 adjustments are applied later (orchestrator step 5)."""
    total = (
        components.recovery
        + components.load
        + components.progression
        + components.marathon_prep
        + components.p3_adjustments
    )
    return int(_clamp(total, 0, 100))


# --------------------------------------------------------------------------- #
# Readiness confidence — §2.4 (moved here in v1.3 C-02)
# --------------------------------------------------------------------------- #

def _parse_date(value: str) -> date:
    if "T" in value:
        return date.fromisoformat(value.split("T", 1)[0])
    return date.fromisoformat(value)


def compute_readiness_confidence(
    state: RunnerState,
    computed: Any,
    params: dict[str, Any],
) -> int:
    """§2.4 — penalties → clamp [0, 100]."""
    penalties = 0
    pen = params["confidence_penalty"]

    if not computed.acwr_reliable:
        penalties += pen["acwr_unreliable"]

    if state.week.avg_weekly_RPE is None:
        penalties += pen["missing_rpe"]

    if state.week.long_run_km_previous_week is None:
        penalties += pen["missing_long_run"]

    if state.week.days_since_last_run > params["long_interruption_days"]:
        penalties += pen["long_interruption"]

    hist_len = len(state.week.weekly_distance_history)
    if hist_len < 4:
        penalties += (4 - hist_len) * pen["per_missing_week"]

    if computed.target_marathon_pace_source == "vma_only":
        penalties += pen["pace_vma_only"]

    if computed.experience_level_source == "declared":
        penalties += pen["experience_declared_only"]

    if state.week.pain_regions and max(p.intensity for p in state.week.pain_regions) > 0:
        penalties += pen["active_pain"]

    submitted = _parse_date(state.meta.submitted_at)
    week_start = _parse_date(state.meta.week_start_date)
    stale_days = (submitted - week_start).days
    if stale_days > params["stale_input_max_days"]:
        penalties += pen["stale_input"]

    return int(_clamp(100 - penalties, 0, 100))
