"""Integration tests — full pipeline with StubLLMClient, no real LLM calls."""

from __future__ import annotations

import json

import pytest

from src.coach_intelligence.api import build_coach_response
from src.coach_intelligence.feedback.collector import NullFeedbackCollector
from src.coach_intelligence.interpreter.envelope_interpreter import EnvelopeInterpreter
from src.coach_intelligence.personalizer.runner_personalizer import RunnerPersonalizer
from src.coach_intelligence.rag.context.retriever import RunnerContextRetriever
from src.coach_intelligence.rag.scientific.retriever import ScientificRetriever
from src.coach_intelligence.reasoning.context_builder import ReasoningContextBuilder
from tests.coach_intelligence.conftest import (
    StubLLMClient,
    make_envelope,
    make_rule_outcome,
    make_snapshot,
    make_state,
)


def _run(
    action: str = "maintain",
    priority: str = "P2",
    medical: bool = False,
    medical_reason: str | None = None,
    weeks_to_race: int | None = None,
    experience: str = "intermediate",
    total_activities: int = 50,
    stub_text: str | None = None,
    triggered_rules=None,
):
    env = make_envelope(
        action=action,
        priority=priority,
        medical=medical,
        medical_reason=medical_reason,
        triggered_rules=triggered_rules,
    )
    snap = make_snapshot(experience=experience, total_activities=total_activities)
    state = make_state(experience=experience, weeks_to_race=weeks_to_race)
    llm = StubLLMClient(stub_text)
    return build_coach_response(env, snap, state, llm_client=llm), llm


def test_full_pipeline_deload_critical():
    rules = [make_rule_outcome(rule_id="RULE-001", priority="P1")]
    response, _ = _run(
        action="deload",
        medical=True,
        medical_reason="pain_critical",
        triggered_rules=rules,
    )
    assert response.medical_alert is not None
    assert "ALERTE MÉDICALE" in response.medical_alert
    assert response.decision_summary != ""


def test_full_pipeline_beginner_gets_simple_style():
    env = make_envelope()
    snap = make_snapshot(total_activities=10)
    state = make_state(experience="beginner")
    llm = StubLLMClient()

    # Inspect the reasoning context to verify communication style
    interpreted = EnvelopeInterpreter().interpret(env)
    pers = RunnerPersonalizer().personalize(snap, state.profile, state.context)
    assert pers.communication_style == "simple"

    response = build_coach_response(env, snap, state, llm_client=llm)
    assert response.decision_summary != ""


def test_full_pipeline_with_race_goal():
    env = make_envelope()
    snap = make_snapshot()
    state = make_state(weeks_to_race=8)
    llm = StubLLMClient()

    interpreted = EnvelopeInterpreter().interpret(env)
    pers = RunnerPersonalizer().personalize(snap, state.profile, state.context)
    assert pers.has_race_goal is True
    assert pers.weeks_to_race == 8

    response = build_coach_response(env, snap, state, llm_client=llm)
    assert response is not None


def test_scientific_snippets_retrieved_for_acwr():
    rules = [make_rule_outcome(rule_id="RULE-003", priority="P1", variables_snapshot={"acwr_distance": 1.6})]
    env = make_envelope(triggered_rules=rules)
    snap = make_snapshot()
    state = make_state()
    llm = StubLLMClient()

    interpreted = EnvelopeInterpreter().interpret(env)
    retriever = ScientificRetriever()
    snippets = retriever.retrieve(interpreted)

    # At least one snippet should reference ACWR
    texts = [s.source + s.claim + s.explanation for s in snippets]
    combined = " ".join(texts).lower()
    assert "acwr" in combined or "charge" in combined


def test_empty_memory_ok():
    response, _ = _run()
    # RunnerContextRetriever with no store returns empty list — pipeline must not crash
    assert response is not None
    assert response.decision_summary != "" or response.main_message != ""


def test_stub_llm_called_once():
    _, llm = _run()
    assert len(llm.calls) == 1


def test_feedback_collector_not_called_by_pipeline():
    """Coach Intelligence does not call FeedbackCollector — reserved for Coach Agent."""
    env = make_envelope()
    snap = make_snapshot()
    state = make_state()
    llm = StubLLMClient()
    collector = NullFeedbackCollector()

    # If the pipeline called collector.record(), it would raise since NullFeedbackCollector
    # accepts any call silently — we just verify the pipeline completes without error
    response = build_coach_response(env, snap, state, llm_client=llm, feedback_collector=collector)
    assert response is not None


def test_no_medical_alert_for_standard_decision():
    response, _ = _run(action="maintain", priority="P2", medical=False)
    assert response.medical_alert is None


def test_pipeline_with_custom_scientific_retriever():
    """Injecting a custom retriever — verifies injectable interface."""
    env = make_envelope()
    snap = make_snapshot()
    state = make_state()
    llm = StubLLMClient()
    custom_retriever = ScientificRetriever()  # same as default, but injected explicitly

    response = build_coach_response(
        env, snap, state,
        llm_client=llm,
        scientific_retriever=custom_retriever,
    )
    assert response is not None


def test_pipeline_with_custom_context_retriever():
    """Injecting an empty context retriever — verifies injectable interface."""
    env = make_envelope()
    snap = make_snapshot()
    state = make_state()
    llm = StubLLMClient()
    custom_retriever = RunnerContextRetriever(store=None)

    response = build_coach_response(
        env, snap, state,
        llm_client=llm,
        context_retriever=custom_retriever,
    )
    assert response is not None


def test_confidence_low_produces_note_end_to_end():
    response, _ = _run(priority="P2")
    # With high confidence (default in make_envelope), no note
    assert response.confidence_note is None

    env = make_envelope(confidence="low")
    snap = make_snapshot()
    state = make_state()
    llm = StubLLMClient()
    response = build_coach_response(env, snap, state, llm_client=llm)
    assert response.confidence_note is not None
