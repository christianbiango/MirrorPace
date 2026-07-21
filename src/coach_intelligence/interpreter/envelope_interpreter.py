from __future__ import annotations

from src.knowledge_engine.api import DecisionEnvelope, RuleOutcome

from ..domain.schemas.interpreted_decision import Confidence, InterpretedDecision, Severity

_PRIORITY_SEVERITY: dict[str, Severity] = {
    "P0": "critical",
    "P1": "critical",
    "P2": "warning",
    "P3": "informational",
    "P4": "informational",
}

_CONFIDENCE_MAP: dict[str, Confidence] = {
    "high": "high",
    "medium": "medium",
    "low": "low",
}


def _find_dominant_rule_ids(triggered: list[RuleOutcome]) -> list[str]:
    if not triggered:
        return []
    top_priority = min(r.priority for r in triggered)
    return [r.rule_id for r in triggered if r.priority == top_priority]


def _extract_key_metrics(envelope: DecisionEnvelope, triggered: list[RuleOutcome]) -> dict:
    metrics: dict = {
        "readiness_score": envelope.readiness.score,
        "readiness_confidence": envelope.readiness.confidence_score,
        "delta_pct": envelope.decision.delta_pct,
        "action": envelope.decision.action,
        "absolute_target_km": envelope.decision.absolute_next_week_target_km,
    }
    for rule in triggered:
        if "acwr_distance" in rule.variables_snapshot:
            metrics["acwr"] = rule.variables_snapshot["acwr_distance"]
            break
    return metrics


class EnvelopeInterpreter:
    def interpret(self, envelope: DecisionEnvelope) -> InterpretedDecision:
        triggered = envelope.triggered_rules
        dominant_ids = _find_dominant_rule_ids(triggered)

        if triggered:
            top_priority = min(r.priority for r in triggered)
            severity: Severity = _PRIORITY_SEVERITY.get(top_priority, "informational")
        else:
            severity = "informational"

        # Medical flag always overrides to critical
        if envelope.medical_referral:
            severity = "critical"

        reasons = envelope.llm_context.reasons_human_readable
        primary_reason = reasons[0] if reasons else ""
        supporting_reasons = reasons[1:] if len(reasons) > 1 else []

        confidence: Confidence = _CONFIDENCE_MAP.get(
            envelope.llm_context.confidence_caveat, "high"
        )

        return InterpretedDecision(
            action=envelope.decision.action,
            severity=severity,
            primary_reason=primary_reason,
            supporting_reasons=supporting_reasons,
            dominant_rule_ids=dominant_ids,
            plan_hints=envelope.plan_hints,
            medical_flag=envelope.medical_referral,
            medical_reason=envelope.medical_referral_reason,
            confidence=confidence,
            key_metrics=_extract_key_metrics(envelope, triggered),
        )
