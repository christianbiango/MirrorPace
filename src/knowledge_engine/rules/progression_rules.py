"""P1..P3 progression / recovery / green-light rules.

- P1: RULE-004, RULE-005, RULE-006, RULE-007, RULE-026
- P2: RULE-008, RULE-009, RULE-010
- P3: RULE-011 (v1.3 C-01 guard), RULE-012
"""

from __future__ import annotations

from ..config.loader import EngineConfig
from ..domain.schemas.computed import ComputedVariables
from ..domain.schemas.rule_outcome import RuleOutcome
from ..domain.schemas.runner_state import RunnerState
from .base import RuleSpec, not_triggered, snapshot


# --------------------------------------------------------------------------- #
# P1
# --------------------------------------------------------------------------- #

def rule_004(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    """RULE-004 — ACWR élevé (block_increase)."""
    lo = cfg.get("acwr_block_threshold")
    hi = cfg.get("acwr_deload_threshold")
    if (
        computed.acwr_reliable
        and computed.acwr_distance is not None
        and lo < computed.acwr_distance < hi
    ):
        return RuleOutcome(
            rule_id="RULE-004",
            priority="P1",
            triggered=True,
            action="block_increase",
            reason=f"ACWR {computed.acwr_distance:.2f} — zone à risque",
            params_used={"acwr_block_threshold": lo, "acwr_deload_threshold": hi},
            variables_snapshot=snapshot(acwr_distance=computed.acwr_distance),
        )
    return not_triggered("RULE-004", "P1")


def rule_005(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    """RULE-005 — Progression volume > cap%."""
    cap = cfg.get("weekly_increase_cap_pct")
    if (
        computed.delta_volume_reliable
        and computed.delta_volume_pct is not None
        and computed.delta_volume_pct > cap
    ):
        return RuleOutcome(
            rule_id="RULE-005",
            priority="P1",
            triggered=True,
            action="block_increase",
            reason=f"Δvolume {computed.delta_volume_pct:.1f}% > {cap}%",
            params_used={"weekly_increase_cap_pct": cap},
            variables_snapshot=snapshot(delta_volume_pct=computed.delta_volume_pct),
        )
    return not_triggered("RULE-005", "P1")


def rule_006(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    """RULE-006 — Récupération insuffisante (fatigue high AND sleep low) OR fatigue extreme."""
    fat_high = cfg.get("fatigue_high_threshold")
    fat_ext = cfg.get("fatigue_extreme_threshold")
    sleep_low = cfg.get("sleep_low_threshold")

    fat = state.week.fatigue_score
    sleep = state.week.sleep_quality_score

    if (fat >= fat_high and sleep <= sleep_low) or fat >= fat_ext:
        return RuleOutcome(
            rule_id="RULE-006",
            priority="P1",
            triggered=True,
            action="block_increase",
            reason=f"Fatigue={fat} / sommeil={sleep} — récupération insuffisante",
            params_used={
                "fatigue_high_threshold": fat_high,
                "fatigue_extreme_threshold": fat_ext,
                "sleep_low_threshold": sleep_low,
            },
            variables_snapshot=snapshot(fatigue_score=fat, sleep_quality_score=sleep),
        )
    return not_triggered("RULE-006", "P1")


def rule_007(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    """RULE-007 — Phase taper : décrément forcé (force_decrease)."""
    if state.context.current_phase != "taper":
        return not_triggered("RULE-007", "P1")

    reduction_min = cfg.get("taper_volume_reduction_min")
    reduction_max = cfg.get("taper_volume_reduction_max")
    target_delta = -(reduction_min + reduction_max) / 2.0  # midpoint of range

    return RuleOutcome(
        rule_id="RULE-007",
        priority="P1",
        triggered=True,
        action="force_decrease",
        target_delta_pct=target_delta,
        reason=(
            f"Phase taper : {target_delta:.0f}% volume dans "
            f"[-{reduction_max}, -{reduction_min}]%, intensité maintenue"
        ),
        params_used={
            "taper_volume_reduction_min": reduction_min,
            "taper_volume_reduction_max": reduction_max,
        },
        extras={"target_delta_range": (-reduction_max, -reduction_min)},
    )


def rule_026(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    """RULE-026 — Retour d'interruption (>N days)."""
    threshold = cfg.get("interruption_threshold_days")
    if state.week.days_since_last_run > threshold:
        return RuleOutcome(
            rule_id="RULE-026",
            priority="P1",
            triggered=True,
            action="block_increase",
            plan_hint="return_from_interruption_progressive",
            reason=(
                f"Interruption {state.week.days_since_last_run}j "
                f"> {threshold}j — reprise progressive"
            ),
            params_used={"interruption_threshold_days": threshold},
            variables_snapshot=snapshot(days_since_last_run=state.week.days_since_last_run),
        )
    return not_triggered("RULE-026", "P1")


# --------------------------------------------------------------------------- #
# P2
# --------------------------------------------------------------------------- #

def rule_008(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    """RULE-008 — Blessure récente (cap_increase)."""
    weeks_cap = cfg.get("recent_injury_cap_weeks")
    cap_pct = cfg.get("recent_injury_max_increase_pct")
    wsli = state.context.weeks_since_last_injury

    if wsli is not None and wsli < weeks_cap:
        return RuleOutcome(
            rule_id="RULE-008",
            priority="P2",
            triggered=True,
            action="cap_increase",
            cap_pct=cap_pct,
            reason=f"Blessure il y a {wsli} semaines — cap +{cap_pct}%",
            params_used={
                "recent_injury_cap_weeks": weeks_cap,
                "recent_injury_max_increase_pct": cap_pct,
            },
            variables_snapshot=snapshot(weeks_since_last_injury=wsli),
        )
    return not_triggered("RULE-008", "P2")


def rule_009(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    """RULE-009 — Fatigue/sommeil modéré (cap_increase)."""
    fat_mod = cfg.get("fatigue_moderate_value")
    sleep_mod = cfg.get("sleep_moderate_value")
    cap_pct = cfg.get("moderate_fatigue_cap_pct")

    fat = state.week.fatigue_score
    sleep = state.week.sleep_quality_score
    if fat == fat_mod or sleep == sleep_mod:
        return RuleOutcome(
            rule_id="RULE-009",
            priority="P2",
            triggered=True,
            action="cap_increase",
            cap_pct=cap_pct,
            reason=f"Fatigue={fat} ou sommeil={sleep} modéré — cap +{cap_pct}%",
            params_used={
                "fatigue_moderate_value": fat_mod,
                "sleep_moderate_value": sleep_mod,
                "moderate_fatigue_cap_pct": cap_pct,
            },
        )
    return not_triggered("RULE-009", "P2")


def rule_010(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    """RULE-010 — Beginner cap (cap_increase)."""
    cap_pct = cfg.get("beginner_max_increase_pct")
    if computed.experience_level == "beginner":
        return RuleOutcome(
            rule_id="RULE-010",
            priority="P2",
            triggered=True,
            action="cap_increase",
            cap_pct=cap_pct,
            reason=f"Coureur débutant — cap +{cap_pct}%",
            params_used={"beginner_max_increase_pct": cap_pct},
            variables_snapshot=snapshot(experience_level=computed.experience_level),
        )
    return not_triggered("RULE-010", "P2")


# --------------------------------------------------------------------------- #
# P3
# --------------------------------------------------------------------------- #

def rule_011(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    """RULE-011 — Feu vert multi-critères (v1.3 C-01 : + guard acwr_reliable)."""
    bonus = cfg.get("green_light_bonus_pts")
    ssm_lo = cfg.get("acwr_sweet_spot_min")
    ssm_hi = cfg.get("acwr_sweet_spot_max")
    fat_low = cfg.get("fatigue_low_threshold")
    sleep_high = cfg.get("sleep_high_threshold")
    pain_ok = cfg.get("pain_ok_threshold")

    if not computed.acwr_reliable:  # v1.3 C-01
        return not_triggered("RULE-011", "P3")
    if computed.acwr_distance is None:
        return not_triggered("RULE-011", "P3")
    if not (ssm_lo <= computed.acwr_distance <= ssm_hi):
        return not_triggered("RULE-011", "P3")
    if state.week.fatigue_score > fat_low:
        return not_triggered("RULE-011", "P3")
    if state.week.sleep_quality_score < sleep_high:
        return not_triggered("RULE-011", "P3")
    max_pain = max((p.intensity for p in state.week.pain_regions), default=0)
    if max_pain > pain_ok:
        return not_triggered("RULE-011", "P3")

    return RuleOutcome(
        rule_id="RULE-011",
        priority="P3",
        triggered=True,
        action="score_adjust",
        score_delta=+bonus,
        reason=f"Feu vert multi-critères — bonus +{bonus} pts",
        params_used={
            "acwr_sweet_spot_min": ssm_lo,
            "acwr_sweet_spot_max": ssm_hi,
            "fatigue_low_threshold": fat_low,
            "sleep_high_threshold": sleep_high,
            "pain_ok_threshold": pain_ok,
            "green_light_bonus_pts": bonus,
        },
        variables_snapshot=snapshot(
            acwr_distance=computed.acwr_distance,
            acwr_reliable=computed.acwr_reliable,
            fatigue_score=state.week.fatigue_score,
            sleep_quality_score=state.week.sleep_quality_score,
            max_pain_intensity=max_pain,
        ),
    )


def rule_012(state: RunnerState, computed: ComputedVariables, cfg: EngineConfig) -> RuleOutcome:
    """RULE-012 — Tolérance avancée."""
    bonus = cfg.get("advanced_tolerance_bonus_pts")
    ssm_lo = cfg.get("acwr_sweet_spot_min")
    ssm_hi = cfg.get("acwr_sweet_spot_max")

    if computed.experience_level != "advanced":
        return not_triggered("RULE-012", "P3")
    if computed.acwr_distance is None:
        return not_triggered("RULE-012", "P3")
    if not (ssm_lo <= computed.acwr_distance <= ssm_hi):
        return not_triggered("RULE-012", "P3")

    return RuleOutcome(
        rule_id="RULE-012",
        priority="P3",
        triggered=True,
        action="score_adjust",
        score_delta=+bonus,
        reason=f"Coureur avancé + ACWR sweet spot — bonus +{bonus} pts",
        params_used={
            "advanced_tolerance_bonus_pts": bonus,
            "acwr_sweet_spot_min": ssm_lo,
            "acwr_sweet_spot_max": ssm_hi,
        },
    )


PROGRESSION_RULES: list[RuleSpec] = [
    # P1
    RuleSpec("RULE-004", "P1", rule_004),
    RuleSpec("RULE-005", "P1", rule_005),
    RuleSpec("RULE-006", "P1", rule_006),
    RuleSpec("RULE-007", "P1", rule_007),
    RuleSpec("RULE-026", "P1", rule_026),
    # P2
    RuleSpec("RULE-008", "P2", rule_008),
    RuleSpec("RULE-009", "P2", rule_009),
    RuleSpec("RULE-010", "P2", rule_010),
    # P3
    RuleSpec("RULE-011", "P3", rule_011),
    RuleSpec("RULE-012", "P3", rule_012),
]
