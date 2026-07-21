"""P4 race-day rules — RULE-023 (pacing), RULE-025 (nutrition). RULE-024 = V2."""

from __future__ import annotations

from ..config.loader import EngineConfig
from ..domain.concepts import MARATHON_DISTANCE_KM
from ..domain.schemas.computed import ComputedVariables
from ..domain.schemas.rule_outcome import RuleOutcome
from ..domain.schemas.runner_state import RunnerState
from .base import RuleSpec, not_triggered


def rule_023(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    """RULE-023 — Pacing jour J (V1 : hint only; requires pace_first_half V2 signal)."""
    return not_triggered("RULE-023", "P4")


def rule_024(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    """RULE-024 — DISABLED_V1 (ambient temperature not modeled)."""
    return not_triggered("RULE-024", "P4")


def rule_025(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    """RULE-025 — Nutrition course : CHO protocol if estimated_race_duration > threshold."""
    threshold_min = cfg.get("cho_protocol_min_duration_min")
    cho_min = cfg.get("cho_min_g_per_hour")
    cho_max = cfg.get("cho_max_g_per_hour")

    target_pace = computed.target_marathon_pace_min_km
    if target_pace is None:
        return not_triggered("RULE-025", "P4")
    estimated_race_duration_min = target_pace * MARATHON_DISTANCE_KM
    if estimated_race_duration_min <= threshold_min:
        return not_triggered("RULE-025", "P4")
    return RuleOutcome(
        rule_id="RULE-025",
        priority="P4",
        triggered=True,
        action="plan_hint",
        plan_hint="cho_protocol_60_90g_per_hour",
        reason=(
            f"Course estimée {estimated_race_duration_min:.0f} min > {threshold_min} min "
            f"— protocole glucides {cho_min}-{cho_max} g/h"
        ),
        params_used={
            "cho_protocol_min_duration_min": threshold_min,
            "cho_min_g_per_hour": cho_min,
            "cho_max_g_per_hour": cho_max,
        },
        extras={
            "cho_min_g_per_hour": cho_min,
            "cho_max_g_per_hour": cho_max,
        },
    )


RACE_DAY_RULES: list[RuleSpec] = [
    RuleSpec("RULE-023", "P4", rule_023),
    RuleSpec("RULE-024", "P4", rule_024),
    RuleSpec("RULE-025", "P4", rule_025),
]
