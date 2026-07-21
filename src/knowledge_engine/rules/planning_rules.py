"""P4 planning rules — RULE-015 to RULE-022 (excluding RULE-017 disabled)."""

from __future__ import annotations

from ..config.loader import EngineConfig
from ..domain.concepts import (
    HALF_MARATHON_DISTANCE_KM,
    MARATHON_DISTANCE_KM,
    TEN_K_DISTANCE_KM,
)
from ..domain.formulas.acwr import coefficient_of_variation
from ..domain.formulas.pace import riegel_predict_marathon_seconds
from ..domain.schemas.computed import ComputedVariables
from ..domain.schemas.rule_outcome import RuleOutcome
from ..domain.schemas.runner_state import RunnerState
from .base import RuleSpec, not_triggered, snapshot


# --------------------------------------------------------------------------- #
# RULE-015 — Structuration macro-plan
# --------------------------------------------------------------------------- #

def rule_015(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    min_weeks = cfg.get("macro_plan_min_weeks")
    cv_max = cfg.get("cv_max_regular")
    weeks_to_race = state.context.weeks_to_race
    history = state.week.weekly_distance_history

    if weeks_to_race is None or weeks_to_race < min_weeks:
        return not_triggered("RULE-015", "P4")
    if len(history) < 4:
        return not_triggered("RULE-015", "P4")
    cv = coefficient_of_variation(history)
    if cv >= cv_max:
        return not_triggered("RULE-015", "P4")

    # Compute suggested phase boundaries (Canova-style split).
    taper = 3
    specific = 8 if weeks_to_race >= 20 else 6
    general = max(weeks_to_race - taper - specific, 0)
    phases = {"general": general, "specific": specific, "taper": taper}

    return RuleOutcome(
        rule_id="RULE-015",
        priority="P4",
        triggered=True,
        action="plan_hint",
        plan_hint="structure_macroplan",
        reason=f"Macro-plan ({weeks_to_race} sem., CV historique {cv:.2f})",
        params_used={"macro_plan_min_weeks": min_weeks, "cv_max_regular": cv_max},
        extras={"plan_type": "macro", "suggested_phases": phases},
    )


# --------------------------------------------------------------------------- #
# RULE-016 — Beginner : cycle préparatoire d'abord
# --------------------------------------------------------------------------- #

def rule_016(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    base_min = cfg.get("beginner_base_min_km")
    if (
        computed.experience_level == "beginner"
        and computed.chronic_load_distance < base_min
    ):
        return RuleOutcome(
            rule_id="RULE-016",
            priority="P4",
            triggered=True,
            action="plan_hint",
            plan_hint="preparatory_cycle_before_marathon_specific",
            reason=(
                f"Débutant + chronic_load {computed.chronic_load_distance:.1f} "
                f"< {base_min} km — cycle préparatoire d'abord"
            ),
            params_used={"beginner_base_min_km": base_min},
        )
    return not_triggered("RULE-016", "P4")


# --------------------------------------------------------------------------- #
# RULE-017 — Sélection plan volume  [DISABLED_V1 — depends on D-05]
# --------------------------------------------------------------------------- #

def rule_017(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    # Blocked by D-05 (experience × chronic_load → plan_level table).
    return not_triggered("RULE-017", "P4")


# --------------------------------------------------------------------------- #
# RULE-018 — Cycle vitesse/seuil pré-marathon
# --------------------------------------------------------------------------- #

def _performances_10k_below_potential(
    target_pace_min_km: float | None,
    recent_race_time_10k: int | None,
    tolerance_pct: float,
    riegel_exponent: float,
) -> bool:
    """[PROD] compare recent_race_time_10k vs Riegel-inverse from target_marathon_pace."""
    if target_pace_min_km is None or recent_race_time_10k is None:
        return False
    # Predicted 10k from target marathon: t_10k = t_marathon * (10 / 42.195) ** exponent
    marathon_time_sec = target_pace_min_km * 60.0 * MARATHON_DISTANCE_KM
    expected_10k_sec = marathon_time_sec * (TEN_K_DISTANCE_KM / MARATHON_DISTANCE_KM) ** riegel_exponent
    if expected_10k_sec == 0:
        return False
    gap = (recent_race_time_10k - expected_10k_sec) / expected_10k_sec * 100
    return gap > tolerance_pct


def rule_018(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    min_weeks_out = cfg.get("speed_cycle_min_weeks_out")
    tolerance = cfg.get("speed_gap_tolerance_pct")
    riegel = cfg.get("riegel_exponent")
    weeks_to_race = state.context.weeks_to_race

    if weeks_to_race is None or weeks_to_race < min_weeks_out:
        return not_triggered("RULE-018", "P4")
    if not _performances_10k_below_potential(
        computed.target_marathon_pace_min_km,
        state.profile.recent_race_time_10k,
        tolerance,
        riegel,
    ):
        return not_triggered("RULE-018", "P4")

    return RuleOutcome(
        rule_id="RULE-018",
        priority="P4",
        triggered=True,
        action="plan_hint",
        plan_hint="speed_threshold_cycle_recommended",
        reason=(
            "10k en deçà du potentiel marathon — cycle vitesse/seuil "
            f"recommandé ({weeks_to_race} sem. avant course)"
        ),
        params_used={
            "speed_cycle_min_weeks_out": min_weeks_out,
            "speed_gap_tolerance_pct": tolerance,
        },
    )


# --------------------------------------------------------------------------- #
# RULE-019 — Objectifs incohérents
# --------------------------------------------------------------------------- #

def rule_019(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    gap_pct = cfg.get("target_realism_gap_pct")
    riegel = cfg.get("riegel_exponent")

    target = state.profile.race_target_time
    half = state.profile.recent_race_time_half
    if target is None or half is None:
        return not_triggered("RULE-019", "P4")

    predicted = riegel_predict_marathon_seconds(half, HALF_MARATHON_DISTANCE_KM, riegel)
    if target == 0:
        return not_triggered("RULE-019", "P4")
    ratio = abs(predicted - target) / target * 100
    if ratio <= gap_pct:
        return not_triggered("RULE-019", "P4")

    return RuleOutcome(
        rule_id="RULE-019",
        priority="P4",
        triggered=True,
        action="plan_hint",
        plan_hint="revise_objectives",
        reason=(
            f"Écart objectif vs Riegel(semi)={ratio:.1f}% > {gap_pct}% — "
            "objectif à réévaluer"
        ),
        params_used={"target_realism_gap_pct": gap_pct, "riegel_exponent": riegel},
        variables_snapshot=snapshot(target_sec=target, predicted_sec=int(predicted)),
    )


# --------------------------------------------------------------------------- #
# RULE-020 — Séances manquées (v1.3 C-07)
# --------------------------------------------------------------------------- #

def rule_020(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    neg_delta = cfg.get("missed_sessions_neg_delta_pct")
    if computed.delta_volume_pct is None:
        return not_triggered("RULE-020", "P4")
    if computed.delta_volume_pct >= -neg_delta:
        return not_triggered("RULE-020", "P4")
    if computed.fatigue_trend not in {"improving", "stable"}:  # v1.3 C-07 : exclude "unknown"
        return not_triggered("RULE-020", "P4")

    return RuleOutcome(
        rule_id="RULE-020",
        priority="P4",
        triggered=True,
        action="plan_hint",
        plan_hint="adjust_next_week_no_catchup",
        reason=(
            f"Δvolume {computed.delta_volume_pct:.1f}% < -{neg_delta}% et "
            f"fatigue {computed.fatigue_trend} — pas de rattrapage"
        ),
        params_used={"missed_sessions_neg_delta_pct": neg_delta},
        variables_snapshot=snapshot(
            delta_volume_pct=computed.delta_volume_pct,
            fatigue_trend=computed.fatigue_trend,
        ),
    )


# --------------------------------------------------------------------------- #
# RULE-021 — Détail taper (planification)
# --------------------------------------------------------------------------- #

def rule_021(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    if state.context.current_phase != "taper":
        return not_triggered("RULE-021", "P4")
    reduction_min = cfg.get("taper_volume_reduction_min")
    reduction_max = cfg.get("taper_volume_reduction_max")
    duration = cfg.get("taper_duration_weeks")
    reduction_pct = (reduction_min + reduction_max) / 2.0
    return RuleOutcome(
        rule_id="RULE-021",
        priority="P4",
        triggered=True,
        action="plan_hint",
        plan_hint="taper_structure",
        reason=f"Taper : -{reduction_pct:.0f}% volume sur {duration} sem., intensité maintenue",
        params_used={
            "taper_volume_reduction_min": reduction_min,
            "taper_volume_reduction_max": reduction_max,
            "taper_duration_weeks": duration,
        },
        extras={
            "volume_reduction_pct": reduction_pct,
            "taper_duration_weeks": duration,
            "keep_intensity": True,
        },
    )


# --------------------------------------------------------------------------- #
# RULE-022 — Calculer allure marathon cible
# --------------------------------------------------------------------------- #

def rule_022(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    """The pace hierarchy already runs in the compute step; this rule only
    reports whether a source was available.
    """
    if computed.target_marathon_pace_min_km is not None:
        return not_triggered("RULE-022", "P4")
    p = state.profile
    if (
        p.recent_race_time_half is None
        and p.recent_race_time_10k is None
        and p.VMA_kmh is None
        and p.race_target_time is None
    ):
        return not_triggered("RULE-022", "P4")
    # If we have inputs but no pace yet, surface a hint.
    return RuleOutcome(
        rule_id="RULE-022",
        priority="P4",
        triggered=True,
        action="plan_hint",
        plan_hint="fill_target_marathon_pace",
        reason="Sources disponibles pour calculer l'allure marathon cible",
    )


PLANNING_RULES: list[RuleSpec] = [
    RuleSpec("RULE-015", "P4", rule_015),
    RuleSpec("RULE-016", "P4", rule_016),
    RuleSpec("RULE-017", "P4", rule_017),  # disabled_v1 handled by rules_status
    RuleSpec("RULE-018", "P4", rule_018),
    RuleSpec("RULE-019", "P4", rule_019),
    RuleSpec("RULE-020", "P4", rule_020),
    RuleSpec("RULE-021", "P4", rule_021),
    RuleSpec("RULE-022", "P4", rule_022),
]
