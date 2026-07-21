from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from src.knowledge_engine.api import PlanHint

Severity = Literal["critical", "warning", "informational"]
Confidence = Literal["high", "medium", "low"]


@dataclass
class InterpretedDecision:
    action: str
    severity: Severity
    primary_reason: str
    supporting_reasons: list[str] = field(default_factory=list)
    dominant_rule_ids: list[str] = field(default_factory=list)
    plan_hints: list[PlanHint] = field(default_factory=list)
    medical_flag: bool = False
    medical_reason: str | None = None
    confidence: Confidence = "high"
    key_metrics: dict = field(default_factory=dict)
