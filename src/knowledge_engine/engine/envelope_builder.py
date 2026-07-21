"""DecisionEnvelope assembler — KB v1.2 §6.2 + v1.3 C-03 + v1.3.1 C-14."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Iterable

from .. import ENGINE_VERSION, SCHEMA_VERSION
from ..config.loader import EngineConfig
from ..domain.schemas.computed import ComputedVariables
from ..domain.schemas.decision import (
    Decision,
    DecisionEnvelope,
    DecisionMeta,
    LlmContext,
    PlanHint,
    ReadinessOut,
)
from ..domain.schemas.rule_outcome import RuleOutcome
from ..domain.schemas.runner_state import RunnerState
from .aggregator import AggregatedDecision


def resolve_medical_referral(
    triggered_rules: Iterable[RuleOutcome],
    pathologies_connues: list[str],
) -> tuple[bool, str | None]:
    """v1.3.1 C-14 — priority: pain_critical > pain_tendon > known_pathology > None."""
    triggered_rules = list(triggered_rules)
    r001 = any(o.rule_id == "RULE-001" and o.triggered for o in triggered_rules)
    r002 = any(o.rule_id == "RULE-002" and o.triggered for o in triggered_rules)

    if r001:
        return True, "pain_critical"
    if r002:
        return True, "pain_tendon"
    if pathologies_connues:
        return True, "known_pathology"
    return False, None


def _round_target(km: float, step: float) -> float:
    """Round to nearest `step` (default 0.5) — D-20."""
    if step <= 0:
        return km
    return math.floor(km / step + 0.5) * step


def _compute_absolute_target(
    action: str,
    weekly_distance_km: float,
    delta_pct: float,
    cfg: EngineConfig,
) -> float:
    raw = weekly_distance_km * (1 + delta_pct / 100.0)
    if action == "maintain":
        floor = cfg.get("min_absolute_weekly_km_on_maintain")  # v1.3 C-09
    else:
        floor = cfg.get("min_absolute_weekly_km")
    raw = max(raw, float(floor))
    return _round_target(raw, cfg.get("target_km_rounding_step"))


def _confidence_caveat(score: int, cfg: EngineConfig) -> str:
    if score >= cfg.get("confidence_min_high"):
        return "high"
    if score >= cfg.get("confidence_min_medium"):
        return "medium"
    return "low"


def build_envelope(
    state: RunnerState,
    computed: ComputedVariables,
    outcomes: list[RuleOutcome],
    aggregated: AggregatedDecision,
    warnings: list[str],
    cfg: EngineConfig,
) -> DecisionEnvelope:
    now_iso = datetime.now(tz=timezone.utc).isoformat()

    # v1.3.1 C-14 — medical_referral resolution
    medical_ref, medical_reason = resolve_medical_referral(
        outcomes, state.profile.pathologies_connues
    )

    # v1.3 C-03 — surface warning if pathology triggered the referral
    warnings = list(warnings)
    if state.profile.pathologies_connues and "medical_referral_recommended" not in warnings:
        warnings.append("medical_referral_recommended")

    # Split triggered vs non-triggered rules
    triggered = [o for o in outcomes if o.triggered]

    # Plan hints collected from P4 (and secondary hints from other priorities e.g. RULE-026)
    plan_hints: list[PlanHint] = []
    for o in triggered:
        if o.plan_hint:
            plan_hints.append(
                PlanHint(rule_id=o.rule_id, hint=o.plan_hint, params=dict(o.extras))
            )

    absolute_target = _compute_absolute_target(
        aggregated.action, state.week.weekly_distance_km, aggregated.delta_pct, cfg
    )

    # Readiness output — includes P3 adjustment already applied by orchestrator
    readiness = ReadinessOut(
        score=computed.readiness_score,
        confidence_score=computed.readiness_confidence_score,
        components={
            "recovery": computed.readiness_component_scores.recovery,
            "load": computed.readiness_component_scores.load,
            "progression": computed.readiness_component_scores.progression,
            "marathon_prep": computed.readiness_component_scores.marathon_prep,
            "p3_adjustments": computed.readiness_component_scores.p3_adjustments,
        },
    )

    reasons_hr = [aggregated.reason] + [o.reason for o in triggered if o.reason]
    caveat = _confidence_caveat(computed.readiness_confidence_score, cfg)
    if caveat != "high":
        reasons_hr.append(f"low_confidence_advice (caveat={caveat})")

    return DecisionEnvelope(
        meta=DecisionMeta(
            engine_version=ENGINE_VERSION,
            config_hash=cfg.config_hash,
            computed_at=now_iso,
            schema_version=SCHEMA_VERSION,
        ),
        decision=Decision(
            action=aggregated.action,
            delta_pct=aggregated.delta_pct,
            delta_pct_range=aggregated.delta_pct_range,
            absolute_next_week_target_km=absolute_target,
        ),
        readiness=readiness,
        triggered_rules=triggered,
        ignored_rules_due_to_short_circuit=aggregated.ignored_due_to_short_circuit,
        warnings=warnings,
        plan_hints=plan_hints,
        medical_referral=medical_ref,
        medical_referral_reason=medical_reason,
        llm_context=LlmContext(
            reasons_human_readable=reasons_hr,
            confidence_caveat=caveat,
        ),
    )
