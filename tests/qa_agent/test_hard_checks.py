"""Unit tests for hard_checks — deterministic, no LLM calls."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.coach_agent.domain.intent import AgentResponse
from src.knowledge_engine.domain.schemas.decision import (
    Decision,
    DecisionEnvelope,
    DecisionMeta,
    LlmContext,
    ReadinessOut,
)
from src.knowledge_engine.domain.schemas.rule_outcome import RuleOutcome
from src.qa_agent.domain.schemas.conversation_log import ConversationEntry, ConversationLog
from src.qa_agent.domain.schemas.runner_profile import RunnerProfile
from src.qa_agent.evaluation.hard_checks import (
    check_ke_coherence,
    check_medical_flag,
    check_memory_utilization,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _profile() -> RunnerProfile:
    return RunnerProfile(
        id="test",
        display_name="Test",
        system_prompt="",
        opening_messages=["test"],
        expected_intents=[],
    )


def _response(text: str) -> AgentResponse:
    return AgentResponse(
        text=text,
        intent="ANALYSIS_REQUEST",
        session_id="s1",
        turn_number=1,
    )


def _envelope(action: str, medical_referral: bool = False) -> DecisionEnvelope:
    return DecisionEnvelope(
        meta=DecisionMeta(
            engine_version="1.3.1",
            config_hash="abc",
            computed_at="2026-07-22T00:00:00Z",
            schema_version="1.0",
        ),
        decision=Decision(
            action=action,
            delta_pct=-20.0,
            delta_pct_range=(-25.0, -15.0),
            absolute_next_week_target_km=30.0,
        ),
        readiness=ReadinessOut(score=55, confidence_score=80),
        triggered_rules=[],
        medical_referral=medical_referral,
        medical_referral_reason="test_reason" if medical_referral else None,
        llm_context=LlmContext(),
    )


def _log(entries: list[ConversationEntry], runner_id: str | None = None) -> ConversationLog:
    return ConversationLog(
        conversation_id="qa-test",
        runner_profile=_profile(),
        entries=entries,
        termination_reason="satisfied",
        started_at="2026-07-22T00:00:00Z",
        ended_at="2026-07-22T00:05:00Z",
        runner_id=runner_id,
    )


# ── KE coherence ─────────────────────────────────────────────────────────────

def test_ke_coherence_passes_when_aligned():
    entry = ConversationEntry(
        turn_number=1,
        user_message="analyse",
        agent_response=_response("Je te recommande de réduire ta charge cette semaine."),
        envelope_snapshot=_envelope("deload"),
    )
    assert check_ke_coherence(_log([entry])) == []


def test_ke_coherence_fails_when_coach_says_increase_on_deload():
    entry = ConversationEntry(
        turn_number=1,
        user_message="analyse",
        agent_response=_response("Tu peux augmenter le volume sans problème."),
        envelope_snapshot=_envelope("deload"),
    )
    failures = check_ke_coherence(_log([entry]))
    assert len(failures) == 1
    assert "ke_contradiction_turn_1" in failures[0]
    assert "deload" in failures[0]


def test_ke_coherence_fails_when_coach_says_augment_on_decrease():
    entry = ConversationEntry(
        turn_number=2,
        user_message="ok",
        agent_response=_response("N'hésite pas à augmenter ta charge la semaine prochaine."),
        envelope_snapshot=_envelope("decrease"),
    )
    failures = check_ke_coherence(_log([entry]))
    assert len(failures) == 1
    assert "ke_contradiction_turn_2" in failures[0]


def test_ke_coherence_no_failure_without_envelope():
    entry = ConversationEntry(
        turn_number=1,
        user_message="pourquoi ?",
        agent_response=_response("augmenter le volume serait risqué maintenant"),
        envelope_snapshot=None,
    )
    assert check_ke_coherence(_log([entry])) == []


def test_ke_coherence_maintain_is_neutral():
    entry = ConversationEntry(
        turn_number=1,
        user_message="analyse",
        agent_response=_response("Maintiens ton volume actuel."),
        envelope_snapshot=_envelope("maintain"),
    )
    assert check_ke_coherence(_log([entry])) == []


# ── Medical flag ──────────────────────────────────────────────────────────────

def test_medical_flag_passes_when_coach_mentions_doctor():
    entry = ConversationEntry(
        turn_number=1,
        user_message="analyse",
        agent_response=_response("Je te conseille de consulter un médecin avant de continuer."),
        envelope_snapshot=_envelope("deload", medical_referral=True),
    )
    assert check_medical_flag(_log([entry])) == []


def test_medical_flag_fails_when_coach_ignores_referral():
    entry = ConversationEntry(
        turn_number=1,
        user_message="analyse",
        agent_response=_response("Réduire ta charge cette semaine serait la bonne décision."),
        envelope_snapshot=_envelope("deload", medical_referral=True),
    )
    failures = check_medical_flag(_log([entry]))
    assert len(failures) == 1
    assert "medical_flag_missed" in failures[0]


def test_medical_flag_no_failure_when_not_flagged():
    entry = ConversationEntry(
        turn_number=1,
        user_message="analyse",
        agent_response=_response("Tout va bien cette semaine."),
        envelope_snapshot=_envelope("maintain", medical_referral=False),
    )
    assert check_medical_flag(_log([entry])) == []


# ── Memory utilization ────────────────────────────────────────────────────────

def test_memory_utilization_skips_when_no_runner_id():
    memory_store = MagicMock()
    entry = ConversationEntry(
        turn_number=1,
        user_message="analyse",
        agent_response=_response("Bonne semaine."),
        envelope_snapshot=None,
    )
    result = check_memory_utilization(_log([entry], runner_id=None), memory_store)
    assert result == []
    memory_store.get_decisions.assert_not_called()


def test_memory_utilization_passes_when_no_past_decisions():
    memory_store = MagicMock()
    memory_store.get_decisions.return_value = []
    entry = ConversationEntry(
        turn_number=1,
        user_message="analyse",
        agent_response=_response("Bonne semaine."),
        envelope_snapshot=None,
    )
    result = check_memory_utilization(_log([entry], runner_id="runner-1"), memory_store)
    assert result == []


def test_memory_utilization_fails_when_decisions_exist_but_not_referenced():
    memory_store = MagicMock()
    past_decision = MagicMock()
    memory_store.get_decisions.return_value = [past_decision]
    entry = ConversationEntry(
        turn_number=1,
        user_message="analyse",
        agent_response=_response("Voici l'analyse de ta semaine."),
        envelope_snapshot=None,
    )
    failures = check_memory_utilization(_log([entry], runner_id="runner-1"), memory_store)
    assert len(failures) == 1
    assert "memory_not_utilized" in failures[0]


def test_memory_utilization_passes_when_memory_referenced():
    memory_store = MagicMock()
    memory_store.get_decisions.return_value = [MagicMock()]
    entry = ConversationEntry(
        turn_number=1,
        user_message="analyse",
        agent_response=_response("En regardant l'historique de tes décisions passées, je vois que..."),
        envelope_snapshot=None,
    )
    result = check_memory_utilization(_log([entry], runner_id="runner-1"), memory_store)
    assert result == []
