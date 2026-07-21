"""DecisionEnvelope — KB v1.2 §6.2 + v1.3 C-03 (medical_referral_reason)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .rule_outcome import RuleOutcome


@dataclass
class DecisionMeta:
    engine_version: str
    config_hash: str
    computed_at: str  # ISO-8601
    schema_version: str


@dataclass
class Decision:
    action: str  # deload | decrease | maintain | slight_increase | increase
    delta_pct: float
    delta_pct_range: tuple[float, float]
    absolute_next_week_target_km: float


@dataclass
class ReadinessOut:
    score: int
    confidence_score: int  # v1.3 C-02
    components: dict[str, int] = field(default_factory=dict)


@dataclass
class PlanHint:
    rule_id: str
    hint: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class LlmContext:
    reasons_human_readable: list[str] = field(default_factory=list)
    confidence_caveat: str = "high"  # high | medium | low


@dataclass
class DecisionEnvelope:
    meta: DecisionMeta
    decision: Decision
    readiness: ReadinessOut
    triggered_rules: list[RuleOutcome] = field(default_factory=list)
    ignored_rules_due_to_short_circuit: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    plan_hints: list[PlanHint] = field(default_factory=list)
    medical_referral: bool = False
    medical_referral_reason: str | None = None  # v1.3 C-03 + v1.3.1 C-14
    llm_context: LlmContext = field(default_factory=LlmContext)
