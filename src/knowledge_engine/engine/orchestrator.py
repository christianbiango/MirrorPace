"""Engine pipeline — KB v1.2 §3.99 as amended by v1.3 §4.5 and v1.3.1 C-15.

Order:
  1. Validate → errors/warnings
  2. Compute (ComputedVariables + readiness_confidence_score  — v1.3 C-02)
  3. Fire all rules by priority
  4. Aggregate with GF-06 (v1.3.1 C-13, C-15a)
  5. Apply P3 score adjustments
  6. Collect P4 plan hints (already surfaced through envelope_builder)
  7. Build DecisionEnvelope (medical_referral, warnings, llm_context)
  8. Return
"""

from __future__ import annotations

from ..config.loader import EngineConfig, load_default_config
from ..domain.formulas.acwr import (
    compute_acwr,
    compute_chronic_load,
    compute_delta_long_run_pct,
    compute_delta_volume_pct,
    compute_progression_slope_km_per_week,
)
from ..domain.formulas.experience_level import compute_experience_level
from ..domain.formulas.fatigue_trend import compute_fatigue_trend
from ..domain.formulas.pace import compute_target_marathon_pace
from ..domain.formulas.readiness import (
    compose_readiness_score,
    compute_component_scores,
    compute_readiness_confidence,
)
from ..domain.schemas.computed import ComputedVariables
from ..domain.schemas.decision import DecisionEnvelope
from ..domain.schemas.rule_outcome import RuleOutcome
from ..domain.schemas.runner_state import RunnerState
from ..rules.registry import ALL_RULES
from .aggregator import aggregate, apply_p3_adjustments
from .envelope_builder import build_envelope
from .validator import ValidationError, validate


# --------------------------------------------------------------------------- #
# Compute step
# --------------------------------------------------------------------------- #

def _compute_variables(state: RunnerState, cfg: EngineConfig) -> ComputedVariables:
    params = cfg.thresholds
    week = state.week

    # ACWR pipeline
    chronic_load, reliable_pre_gate = compute_chronic_load(
        week.weekly_distance_history, week.weekly_distance_km, params
    )
    acwr, acwr_reliable = compute_acwr(
        week.weekly_distance_km, chronic_load, reliable_pre_gate, params
    )

    # Volume deltas
    delta_pct, delta_reliable = compute_delta_volume_pct(
        week.weekly_distance_km, week.previous_week_distance_km, params
    )
    delta_long_run_pct = compute_delta_long_run_pct(
        week.long_run_km_last_week, week.long_run_km_previous_week
    )

    # Internal load (renamed § 5.2)
    if week.avg_weekly_RPE is None:
        estimated_internal_load: float | None = None
    else:
        estimated_internal_load = week.avg_weekly_RPE * week.weekly_duration_min

    # Experience level (needs chronic_load already computed)
    experience_level, experience_level_source = compute_experience_level(
        state.profile, chronic_load, params
    )

    # Pace hierarchy
    pace, pace_source, _pace_warnings = compute_target_marathon_pace(
        state.profile, experience_level, params
    )

    # Fatigue trend (v1.3.1 C-12)
    fatigue_trend = compute_fatigue_trend(week.fatigue_score_history)

    # Progression slope
    slope = compute_progression_slope_km_per_week(week.weekly_distance_history)

    zero_volume_week = week.weekly_distance_km == 0

    computed = ComputedVariables(
        chronic_load_distance=chronic_load,
        acwr_distance=acwr,
        acwr_reliable=acwr_reliable,
        delta_volume_pct=delta_pct,
        delta_volume_reliable=delta_reliable,
        delta_long_run_pct=delta_long_run_pct,
        estimated_internal_load=estimated_internal_load,
        estimated_internal_load_notice="aggregated_RPE_estimate",
        target_marathon_pace_min_km=pace,
        target_marathon_pace_source=pace_source,
        experience_level=experience_level,
        experience_level_source=experience_level_source,
        fatigue_trend=fatigue_trend,
        progression_slope_km_per_week=slope,
        zero_volume_week=zero_volume_week,
    )

    # Readiness components (P3 adjustments applied later)
    components = compute_component_scores(state, computed, params)
    computed.readiness_component_scores = components
    computed.readiness_score = compose_readiness_score(components)

    # v1.3 C-02 — confidence lives in step 2
    computed.readiness_confidence_score = compute_readiness_confidence(
        state, computed, params
    )

    return computed


# --------------------------------------------------------------------------- #
# Fire step
# --------------------------------------------------------------------------- #

def _fire_rules(
    state: RunnerState, computed: ComputedVariables, cfg: EngineConfig
) -> list[RuleOutcome]:
    outcomes: list[RuleOutcome] = []
    priority_short_circuited = False
    for spec in ALL_RULES:
        if not cfg.is_rule_active(spec.rule_id):
            outcomes.append(
                RuleOutcome(
                    rule_id=spec.rule_id,
                    priority=spec.priority,
                    triggered=False,
                    action=None,
                    reason="disabled_v1",
                )
            )
            continue
        outcome = spec.fn(state, computed, cfg)
        outcomes.append(outcome)
    return outcomes


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def run_engine(
    state: RunnerState, cfg: EngineConfig | None = None
) -> DecisionEnvelope:
    """Full pipeline. Raises `ValidationError` if input is malformed."""
    if cfg is None:
        cfg = load_default_config()

    # 1. Validate
    report = validate(state, cfg.thresholds)
    if not report.ok():
        raise ValidationError(report)

    # 2. Compute (incl. readiness_confidence_score — v1.3 C-02)
    computed = _compute_variables(state, cfg)

    # 3. Fire rules
    outcomes = _fire_rules(state, computed, cfg)

    # 4. Aggregate (GF-06 applied here, C-15a P0 guard inside)
    aggregated = aggregate(state, computed, outcomes, cfg)

    # 5. P3 score adjustments
    p3_delta = apply_p3_adjustments(outcomes, cfg)
    computed.readiness_component_scores.p3_adjustments = p3_delta
    computed.readiness_score = compose_readiness_score(
        computed.readiness_component_scores
    )

    # 6. P4 plan hints — collected in envelope builder from triggered outcomes
    # 7. Build envelope
    envelope = build_envelope(
        state=state,
        computed=computed,
        outcomes=outcomes,
        aggregated=aggregated,
        warnings=[*report.warnings],
        cfg=cfg,
    )

    # Additional invariant: GF-07 assertion post-agg (v1.3.1 C-15b)
    if state.context.current_phase == "taper":
        p0_triggered = any(
            o.priority == "P0" and o.triggered for o in outcomes
        )
        if p0_triggered:
            assert envelope.decision.action == "deload", (
                "GF-07/GF-01: taper + P0 must yield deload"
            )
        else:
            assert envelope.decision.action == "decrease", (
                "GF-07: taper without P0 must yield decrease"
            )

    return envelope
