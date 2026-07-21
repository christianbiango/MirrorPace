"""RuleOutcome — per-rule JSON schema (KB v1.2 §3 output contract)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuleOutcome:
    rule_id: str
    priority: str  # P0..P4
    triggered: bool
    action: str | None = None  # deload | force_decrease | block_increase | cap_increase
    #                             | score_adjust | plan_hint | None
    cap_pct: float | None = None
    score_delta: int | None = None
    target_delta_pct: float | None = None
    plan_hint: str | None = None
    reason: str = ""
    medical_referral: bool = False
    short_circuit: bool = False
    params_used: dict[str, Any] = field(default_factory=dict)
    variables_snapshot: dict[str, Any] = field(default_factory=dict)
    extras: dict[str, Any] = field(default_factory=dict)  # e.g. suggested_phases
