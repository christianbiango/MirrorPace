"""Aggregation step — KB v1.2 §3.99 step 4, updated by v1.3 §4.5 + v1.3.1 C-13, C-15a.

Priority reduction:
  P0 short-circuits everything → deload.
  P1 forced-decrease (RULE-007 in taper) → decrease.
  P1 block_increase → maintain.
  P2 cap_increase (min of caps) → slight_increase.
  Else → increase (default_by_experience_level).

GF-06 is applied here (post-decision, pre-envelope) using min_restrictive,
with the C-15a guard that a P0-driven "deload" is immutable.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config.loader import EngineConfig
from ..domain.schemas.computed import ComputedVariables
from ..domain.schemas.rule_outcome import RuleOutcome
from ..domain.schemas.runner_state import RunnerState
from .severity import min_restrictive


@dataclass
class AggregatedDecision:
    action: str
    delta_pct: float
    delta_pct_range: tuple[float, float]
    reason: str
    ignored_due_to_short_circuit: list[str]
    p0_triggered: bool
    p1_triggered: bool
    p2_triggered: bool
    triggering_rules: list[str]


def _default_delta(action: str, experience_level: str, cfg: EngineConfig) -> tuple[float, tuple[float, float]]:
    bounds = cfg.get("action_bounds")[action]
    if action == "increase":
        by_level = bounds["default_by_experience_level"]
        return float(by_level[experience_level]), (float(bounds["min"]), float(bounds["max"]))
    return float(bounds["default"]), (float(bounds["min"]), float(bounds["max"]))


def _p1_forced_decrease(outcomes: list[RuleOutcome]) -> RuleOutcome | None:
    for o in outcomes:
        if o.priority == "P1" and o.triggered and o.action == "force_decrease":
            return o
    return None


def _rules_by_priority(outcomes: list[RuleOutcome], priority: str) -> list[RuleOutcome]:
    return [o for o in outcomes if o.priority == priority and o.triggered]


def aggregate(
    state: RunnerState,
    computed: ComputedVariables,
    outcomes: list[RuleOutcome],
    cfg: EngineConfig,
) -> AggregatedDecision:
    experience_level = computed.experience_level

    p0 = _rules_by_priority(outcomes, "P0")
    p1 = _rules_by_priority(outcomes, "P1")
    p2 = _rules_by_priority(outcomes, "P2")

    ignored: list[str] = []

    # --- Step 4 core: reduce by priority --- #
    if p0:
        action = "deload"
        delta, drange = _default_delta("deload", experience_level, cfg)
        ignored = [o.rule_id for o in outcomes if o.priority != "P0" and o.triggered]
        triggering = [o.rule_id for o in p0]
        reason = f"P0 déclenchée ({', '.join(triggering)}) → deload"
    elif forced := _p1_forced_decrease(p1):
        action = "decrease"
        if forced.target_delta_pct is not None:
            delta = forced.target_delta_pct
            _, drange = _default_delta("decrease", experience_level, cfg)
            # For taper, the P1 rule provides its own range.
            if "target_delta_range" in forced.extras:
                drange = tuple(forced.extras["target_delta_range"])  # type: ignore[assignment]
        else:
            delta, drange = _default_delta("decrease", experience_level, cfg)
        # P2 caps are ignored (§3.99 resolution v1.1 CONF-009 [PROD])
        ignored = [o.rule_id for o in p2] + [o.rule_id for o in outcomes if o.priority in {"P3", "P4"} and o.triggered]
        triggering = [forced.rule_id]
        reason = f"P1 force_decrease ({forced.rule_id})"
    elif p1:
        action = "maintain"
        delta, drange = _default_delta("maintain", experience_level, cfg)
        ignored = [o.rule_id for o in p2]
        triggering = [o.rule_id for o in p1]
        reason = f"P1 block_increase ({', '.join(triggering)}) → maintain"
    elif p2:
        caps = [o.cap_pct for o in p2 if o.cap_pct is not None]
        _, drange = _default_delta("slight_increase", experience_level, cfg)
        slight_default = cfg.get("action_bounds")["slight_increase"]["default"]
        if caps:
            cap = min(caps)
            delta = min(cap, slight_default)
        else:
            delta = slight_default
        action = "slight_increase"
        triggering = [o.rule_id for o in p2]
        reason = f"P2 cap_increase ({', '.join(triggering)}) — cap={min(caps) if caps else 'n/a'}"
    else:
        action = "increase"
        delta, drange = _default_delta("increase", experience_level, cfg)
        triggering = []
        reason = "Aucune contrainte prioritaire — progression standard"

    # --- GF-06 with C-15a guard: skip when P0 is active --- #
    if not p0:
        if computed.readiness_confidence_score < cfg.get("confidence_min_medium"):
            new_action = min_restrictive(action, "maintain")
            if new_action != action:
                # Reduced to maintain
                action = new_action
                delta, drange = _default_delta(action, experience_level, cfg)
                reason += f" | GF-06: confidence {computed.readiness_confidence_score} < min → maintain"

    return AggregatedDecision(
        action=action,
        delta_pct=float(delta),
        delta_pct_range=(float(drange[0]), float(drange[1])),
        reason=reason,
        ignored_due_to_short_circuit=ignored,
        p0_triggered=bool(p0),
        p1_triggered=bool(p1),
        p2_triggered=bool(p2),
        triggering_rules=triggering,
    )


def apply_p3_adjustments(
    outcomes: list[RuleOutcome], cfg: EngineConfig
) -> int:
    """Return the clamped sum of P3 score deltas (§3.99 step 5)."""
    bounds = cfg.get("readiness_p3_bounds")
    total = sum(
        o.score_delta or 0 for o in outcomes if o.priority == "P3" and o.triggered
    )
    return max(-bounds, min(bounds, total))
