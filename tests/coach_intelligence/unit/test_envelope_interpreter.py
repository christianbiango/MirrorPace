from __future__ import annotations

import pytest

from src.coach_intelligence.interpreter.envelope_interpreter import EnvelopeInterpreter
from tests.coach_intelligence.conftest import make_envelope, make_rule_outcome


@pytest.fixture
def interpreter() -> EnvelopeInterpreter:
    return EnvelopeInterpreter()


def test_p0_is_critical(interpreter):
    env = make_envelope(triggered_rules=[make_rule_outcome(priority="P0")])
    result = interpreter.interpret(env)
    assert result.severity == "critical"


def test_p1_is_critical(interpreter):
    env = make_envelope(triggered_rules=[make_rule_outcome(priority="P1")])
    result = interpreter.interpret(env)
    assert result.severity == "critical"


def test_p2_is_warning(interpreter):
    env = make_envelope(triggered_rules=[make_rule_outcome(priority="P2")])
    result = interpreter.interpret(env)
    assert result.severity == "warning"


def test_p3_is_informational(interpreter):
    env = make_envelope(triggered_rules=[make_rule_outcome(priority="P3")])
    result = interpreter.interpret(env)
    assert result.severity == "informational"


def test_p4_is_informational(interpreter):
    env = make_envelope(triggered_rules=[make_rule_outcome(priority="P4")])
    result = interpreter.interpret(env)
    assert result.severity == "informational"


def test_medical_flag_forces_critical(interpreter):
    # Even P4 rule → critical if medical_referral=True
    env = make_envelope(
        triggered_rules=[make_rule_outcome(priority="P4")],
        medical=True,
        medical_reason="pain_critical",
    )
    result = interpreter.interpret(env)
    assert result.severity == "critical"
    assert result.medical_flag is True
    assert result.medical_reason == "pain_critical"


def test_no_triggered_rules(interpreter):
    env = make_envelope(triggered_rules=[])
    result = interpreter.interpret(env)
    assert result.severity == "informational"
    assert result.dominant_rule_ids == []


def test_dominant_rule_ids_highest_priority_only(interpreter):
    rules = [
        make_rule_outcome(rule_id="RULE-001", priority="P1"),
        make_rule_outcome(rule_id="RULE-002", priority="P1"),
        make_rule_outcome(rule_id="RULE-005", priority="P2"),
    ]
    env = make_envelope(triggered_rules=rules)
    result = interpreter.interpret(env)
    assert set(result.dominant_rule_ids) == {"RULE-001", "RULE-002"}
    assert "RULE-005" not in result.dominant_rule_ids


def test_acwr_extracted_from_variables_snapshot(interpreter):
    rules = [make_rule_outcome(variables_snapshot={"acwr_distance": 1.45})]
    env = make_envelope(triggered_rules=rules)
    result = interpreter.interpret(env)
    assert "acwr" in result.key_metrics
    assert result.key_metrics["acwr"] == pytest.approx(1.45)


def test_no_acwr_when_not_in_snapshot(interpreter):
    env = make_envelope(triggered_rules=[make_rule_outcome(variables_snapshot={})])
    result = interpreter.interpret(env)
    assert "acwr" not in result.key_metrics


def test_confidence_mapping_low(interpreter):
    env = make_envelope(confidence="low")
    result = interpreter.interpret(env)
    assert result.confidence == "low"


def test_confidence_mapping_medium(interpreter):
    env = make_envelope(confidence="medium")
    result = interpreter.interpret(env)
    assert result.confidence == "medium"


def test_action_and_reasons_preserved(interpreter):
    env = make_envelope(action="deload")
    result = interpreter.interpret(env)
    assert result.action == "deload"
    assert result.primary_reason == "primary reason"
    assert "secondary reason" in result.supporting_reasons


def test_key_metrics_contain_readiness(interpreter):
    env = make_envelope()
    result = interpreter.interpret(env)
    assert result.key_metrics["readiness_score"] == 70
    assert result.key_metrics["readiness_confidence"] == 80
    assert result.key_metrics["absolute_target_km"] == 50.0
