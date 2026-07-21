from __future__ import annotations

import json

import pytest

from src.coach_intelligence.domain.schemas.coach_response import RawLLMResponse
from src.coach_intelligence.safety.safety_guard import SafetyGuard
from src.coach_intelligence.interpreter.envelope_interpreter import EnvelopeInterpreter
from src.coach_intelligence.personalizer.runner_personalizer import RunnerPersonalizer
from src.coach_intelligence.reasoning.context_builder import ReasoningContextBuilder
from tests.coach_intelligence.conftest import make_envelope, make_snapshot, make_state


def _make_raw(text: str) -> RawLLMResponse:
    return RawLLMResponse(text=text, model="stub", input_tokens=10, output_tokens=10)


def _make_context(medical: bool = False, medical_reason: str | None = None, confidence: str = "high"):
    env = make_envelope(medical=medical, medical_reason=medical_reason, confidence=confidence)
    snap = make_snapshot()
    state = make_state()
    interp = EnvelopeInterpreter().interpret(env)
    pers = RunnerPersonalizer().personalize(snap, state.profile, state.context)
    return ReasoningContextBuilder().build(interp, pers, [], [])


_VALID_JSON = json.dumps({
    "decision_summary": "Réduire.",
    "main_message": "Message principal.",
    "scientific_context": ["Source A."],
    "personal_context": ["Historique."],
    "plan_hints_formatted": ["Conseil 1."],
})


@pytest.fixture
def guard() -> SafetyGuard:
    return SafetyGuard()


def test_valid_json_parsed(guard):
    ctx = _make_context()
    result = guard.apply(_make_raw(_VALID_JSON), ctx)
    assert result.decision_summary == "Réduire."
    assert result.main_message == "Message principal."
    assert result.scientific_context == ["Source A."]


def test_markdown_json_parsed(guard):
    md = f"```json\n{_VALID_JSON}\n```"
    ctx = _make_context()
    result = guard.apply(_make_raw(md), ctx)
    assert result.decision_summary == "Réduire."


def test_invalid_json_fallback(guard):
    ctx = _make_context()
    result = guard.apply(_make_raw("Texte non-JSON brut."), ctx)
    assert result.main_message == "Texte non-JSON brut."
    assert result.decision_summary == ""
    assert result.scientific_context == []


def test_medical_critical_alert_injected(guard):
    ctx = _make_context(medical=True, medical_reason="pain_critical")
    result = guard.apply(_make_raw(_VALID_JSON), ctx)
    assert result.medical_alert is not None
    assert "ALERTE MÉDICALE" in result.medical_alert


def test_medical_tendon_alert_injected(guard):
    ctx = _make_context(medical=True, medical_reason="pain_tendon")
    result = guard.apply(_make_raw(_VALID_JSON), ctx)
    assert result.medical_alert is not None
    assert "tendineuse" in result.medical_alert


def test_medical_known_pathology_alert(guard):
    ctx = _make_context(medical=True, medical_reason="known_pathology")
    result = guard.apply(_make_raw(_VALID_JSON), ctx)
    assert result.medical_alert is not None
    assert "RAPPEL MÉDICAL" in result.medical_alert


def test_unknown_medical_reason_uses_fallback(guard):
    ctx = _make_context(medical=True, medical_reason="something_unknown")
    result = guard.apply(_make_raw(_VALID_JSON), ctx)
    assert result.medical_alert is not None


def test_no_medical_alert_when_flag_false(guard):
    ctx = _make_context(medical=False)
    result = guard.apply(_make_raw(_VALID_JSON), ctx)
    assert result.medical_alert is None


def test_confidence_low_produces_note(guard):
    ctx = _make_context(confidence="low")
    result = guard.apply(_make_raw(_VALID_JSON), ctx)
    assert result.confidence_note is not None
    assert "low" in result.confidence_note


def test_confidence_medium_produces_note(guard):
    ctx = _make_context(confidence="medium")
    result = guard.apply(_make_raw(_VALID_JSON), ctx)
    assert result.confidence_note is not None


def test_confidence_high_no_note(guard):
    ctx = _make_context(confidence="high")
    result = guard.apply(_make_raw(_VALID_JSON), ctx)
    assert result.confidence_note is None


def test_response_ref_is_deterministic(guard):
    ctx = _make_context()
    r1 = guard.apply(_make_raw(_VALID_JSON), ctx)
    r2 = guard.apply(_make_raw(_VALID_JSON), ctx)
    assert r1.response_ref == r2.response_ref
    assert len(r1.response_ref) == 12


def test_envelope_ref_equals_action(guard):
    ctx = _make_context()
    result = guard.apply(_make_raw(_VALID_JSON), ctx)
    assert result.envelope_ref == ctx.interpreted.action
