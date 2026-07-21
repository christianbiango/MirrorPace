"""P0 safety rules — KB v1.2 §3 RULE-001, RULE-002, RULE-003."""

from __future__ import annotations

from ..config.enums import CRITICAL_PAIN_REGIONS
from ..config.loader import EngineConfig
from ..domain.schemas.computed import ComputedVariables
from ..domain.schemas.rule_outcome import RuleOutcome
from ..domain.schemas.runner_state import RunnerState
from .base import RuleSpec, not_triggered, snapshot


# --------------------------------------------------------------------------- #
# RULE-001 — Douleur critique
# --------------------------------------------------------------------------- #

def rule_001(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    p_intensity = cfg.get("pain_critical_intensity")
    p_days = cfg.get("pain_critical_days")

    for r in state.week.pain_regions:
        if r.intensity >= p_intensity and r.days_persistent >= p_days:
            return RuleOutcome(
                rule_id="RULE-001",
                priority="P0",
                triggered=True,
                action="deload",
                reason=(
                    f"Douleur intensité {r.intensity} pendant "
                    f"{r.days_persistent}j sur {r.region}"
                ),
                medical_referral=True,
                short_circuit=True,
                params_used={
                    "pain_critical_intensity": p_intensity,
                    "pain_critical_days": p_days,
                },
                variables_snapshot=snapshot(
                    region=r.region,
                    intensity=r.intensity,
                    days_persistent=r.days_persistent,
                ),
            )
    return not_triggered("RULE-001", "P0")


# --------------------------------------------------------------------------- #
# RULE-002 — Douleur tendon/articulation
# --------------------------------------------------------------------------- #

def rule_002(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    p_intensity = cfg.get("pain_tendon_intensity")
    p_days = cfg.get("pain_tendon_days")

    for r in state.week.pain_regions:
        if (
            r.region in CRITICAL_PAIN_REGIONS
            and r.intensity >= p_intensity
            and r.days_persistent >= p_days
        ):
            return RuleOutcome(
                rule_id="RULE-002",
                priority="P0",
                triggered=True,
                action="deload",
                reason=f"Zone critique {r.region} — risque tendinopathie",
                medical_referral=True,
                short_circuit=True,
                params_used={
                    "pain_tendon_intensity": p_intensity,
                    "pain_tendon_days": p_days,
                },
                variables_snapshot=snapshot(
                    region=r.region,
                    intensity=r.intensity,
                    days_persistent=r.days_persistent,
                ),
            )
    return not_triggered("RULE-002", "P0")


# --------------------------------------------------------------------------- #
# RULE-003 — ACWR danger
# --------------------------------------------------------------------------- #

def rule_003(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    threshold = cfg.get("acwr_deload_threshold")
    if (
        computed.acwr_reliable
        and computed.acwr_distance is not None
        and computed.acwr_distance >= threshold
    ):
        return RuleOutcome(
            rule_id="RULE-003",
            priority="P0",
            triggered=True,
            action="deload",
            reason=(
                f"ACWR {computed.acwr_distance:.2f} ≥ {threshold} — "
                "charge aiguë ≥ 2× la normale"
            ),
            short_circuit=True,
            params_used={"acwr_deload_threshold": threshold},
            variables_snapshot=snapshot(
                acwr_distance=computed.acwr_distance,
                acwr_reliable=computed.acwr_reliable,
            ),
        )
    return not_triggered("RULE-003", "P0")


SAFETY_RULES: list[RuleSpec] = [
    RuleSpec("RULE-001", "P0", rule_001),
    RuleSpec("RULE-002", "P0", rule_002),
    RuleSpec("RULE-003", "P0", rule_003),
]
