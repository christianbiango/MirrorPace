"""Configuration thresholds — KB v1.2 §4.2 + v1.3 §4.2 additions.

Every numeric threshold used by the engine lives here. No `if x >= 4` in
rules — always `if x >= config.pain_critical_intensity`.

Mirrored by `config/thresholds.yaml` for human documentation; the engine
loads this Python module directly to remain dependency-free.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any

_THRESHOLDS: dict[str, Any] = {
    # ==== ACWR ====
    "acwr_deload_threshold": 2.0,
    "acwr_block_threshold": 1.5,
    "acwr_sweet_spot_min": 0.8,
    "acwr_sweet_spot_max": 1.3,
    "acwr_min_history_weeks": 4,
    "chronic_load_window_weeks": 4,
    "chronic_load_method": "simple_mean",
    "ewma_alpha": 0.13,
    "chronic_load_min_km": 5,
    # ==== PROGRESSION ====
    "weekly_increase_cap_pct": 10,
    "small_volume_threshold_km": 20,
    "long_run_max_increase_km": 2,
    # ==== RECOVERY ====
    "fatigue_high_threshold": 4,
    "fatigue_extreme_threshold": 5,
    "fatigue_moderate_value": 3,
    "fatigue_low_threshold": 2,
    "sleep_low_threshold": 2,
    "sleep_moderate_value": 3,
    "sleep_high_threshold": 4,
    "moderate_fatigue_cap_pct": 5,
    # ==== INJURY ====
    "pain_critical_intensity": 4,
    "pain_critical_days": 2,
    "pain_tendon_intensity": 3,
    "pain_tendon_days": 3,
    "pain_ok_threshold": 2,
    "recent_injury_cap_weeks": 4,
    "recent_injury_max_increase_pct": 5,
    "interruption_threshold_days": 14,
    # ==== PROFILE ====
    "beginner_max_increase_pct": 5,
    "beginner_base_min_km": 25,
    "experience_level_criteria": {
        "intermediate": {
            "min_years_running": 1,
            "min_chronic_load_km": 30,
            "min_longest_race_km": 10,
        },
        "advanced": {
            "min_years_running": 3,
            "min_chronic_load_km": 60,
            "min_longest_race_km": 21.0975,
        },
    },
    # ==== PACE MARATHON ====
    "riegel_exponent": 1.06,
    "vma_marathon_fraction": {
        "beginner": 0.75,
        "intermediate": 0.80,
        "advanced": 0.83,
    },
    "target_realism_gap_pct": 15,
    "speed_gap_tolerance_pct": 5,
    "speed_cycle_min_weeks_out": 12,
    # ==== TAPER ====
    "taper_volume_reduction_min": 40,
    "taper_volume_reduction_max": 60,
    "taper_duration_weeks": 3,
    # ==== READINESS COMPOSITION ====
    "readiness_weights": {
        "recovery": 35,
        "load": 35,
        "progression": 15,
        "marathon_prep": 15,
    },
    "readiness_p3_bounds": 10,
    # ==== READINESS CONFIDENCE ====
    "confidence_penalty": {
        "acwr_unreliable": 15,
        "missing_rpe": 10,
        "missing_long_run": 5,
        "long_interruption": 20,
        "per_missing_week": 5,
        "pace_vma_only": 10,
        "experience_declared_only": 5,
        "active_pain": 5,
        "stale_input": 10,
    },
    "confidence_min_high": 75,
    "confidence_min_medium": 50,
    "stale_input_max_days": 10,
    "long_interruption_days": 14,
    # ==== ACTIONS ====
    "action_bounds": {
        "deload": {"min": -40, "default": -25, "max": -20},
        "decrease": {"min": -20, "default": -10, "max": -5},
        "maintain": {"min": 0, "default": 0, "max": 0},
        "slight_increase": {"min": 2, "default": 3, "max": 5},
        "increase": {
            "min": 5,
            "default_by_experience_level": {
                "beginner": 5,
                "intermediate": 7,
                "advanced": 10,
            },
            "max": 10,
        },
    },
    "min_absolute_weekly_km": 0,
    # v1.3 C-09 addition (D-21)
    "min_absolute_weekly_km_on_maintain": 5,
    # D-20 : arrondi 0.5 km
    "target_km_rounding_step": 0.5,
    # ==== RACE DAY ====
    "blowup_pace_tolerance_pct": 5,
    "heat_threshold_C": 20,
    "heat_pace_penalty_pct": -6,
    "cho_protocol_min_duration_min": 90,
    "cho_min_g_per_hour": 60,
    "cho_max_g_per_hour": 90,
    # ==== PLAN ====
    "macro_plan_min_weeks": 16,
    "cv_max_regular": 0.35,
    "missed_sessions_neg_delta_pct": 20,
    # ==== GREEN LIGHT / TOLERANCE ====
    "green_light_bonus_pts": 10,
    "advanced_tolerance_bonus_pts": 5,
    # ==== VALIDATION (v1.3 C-06) ====
    "max_implicit_speed_kmh": 50.0,
}


def default_thresholds() -> dict[str, Any]:
    """Return a fresh, mutable copy of the default thresholds.

    Deep-copies nested dicts so callers cannot mutate the module baseline.
    """
    import copy

    return copy.deepcopy(_THRESHOLDS)


DEFAULT_THRESHOLDS = MappingProxyType(_THRESHOLDS)
