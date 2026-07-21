"""End-to-end validation of the runner memory loop.

Chain under test:
  MemoryStore (CoachingDecision with actual_outcome)
      → build_runner_context_store (InMemoryVectorStore)
      → RunnerContextRetriever.retrieve()
      → ReasoningContextBuilder.build()
      → build_prompt()          ← "MÉMOIRE COUREUR" section
      → build_coach_response()  ← LLM receives the memory in user_prompt

Scenario: a past week (2026-03-02) with a charge spike (90 km) for a beginner
runner triggered slight_increase. The outcome was negative: knee pain appeared
5 days later. A new analysis with the same context (beginner, slight_increase,
same rules) should surface this memory.
"""

from __future__ import annotations

import pytest

from src.coach_intelligence.api import build_coach_response
from src.coach_intelligence.assembler.prompt_builder import build_prompt
from src.coach_intelligence.interpreter.envelope_interpreter import EnvelopeInterpreter
from src.coach_intelligence.personalizer.runner_personalizer import RunnerPersonalizer
from src.coach_intelligence.rag.context.retriever import RunnerContextRetriever
from src.coach_intelligence.reasoning.context_builder import ReasoningContextBuilder
from src.runner_memory.domain import CoachingDecision, RunnerEvent
from src.runner_memory.indexer import build_runner_context_store
from src.runner_memory.store import MemoryStore
from tests.coach_intelligence.conftest import (
    StubLLMClient,
    make_envelope,
    make_rule_outcome,
    make_snapshot,
    make_state,
)

_RUNNER_ID = "runner-001"
_PAST_OUTCOME = "douleur genou apparue après J+5 — charge trop élevée pour débutant"


def _past_decision() -> CoachingDecision:
    """Realistic past decision: charge spike week, negative outcome."""
    return CoachingDecision(
        id="mem_spike_2026_03_02",
        runner_id=_RUNNER_ID,
        date="2026-03-09",
        week_start="2026-03-02",
        decision_ref="ref_spike_001",
        action="slight_increase",
        primary_reason="Débutant + chronic_load faible — cycle préparatoire",
        dominant_rules=["RULE-009", "RULE-010", "RULE-016"],
        key_metrics_snapshot={
            "weekly_distance_km": 90.2,
            "previous_week_distance_km": 34.6,
            "readiness_score": 35,
            "readiness_confidence": 60,
            "fatigue_score": 3,
            "sleep_quality_score": 3,
            "days_since_last_run": 1,
            "target_next_week_km": 12.0,
        },
        expected_outcome="augmentation progressive de la charge",
        actual_outcome=_PAST_OUTCOME,
        outcome_date="2026-03-14",
        text=(
            "Semaine 2026-03-02 : 90.2km readiness 35/100 fatigue 3/5. "
            "Décision: slight_increase. Raison: débutant chronic_load faible. "
            "Règles: RULE-009 RULE-010 RULE-016. "
            "Résultat: douleur genou apparue après J+5 charge trop élevée débutant."
        ),
    )


def _similar_envelope():
    """Current envelope with same action + same dominant rules as the past decision."""
    return make_envelope(
        action="slight_increase",
        triggered_rules=[
            make_rule_outcome("RULE-009", triggered=True, reason="Fatigue modérée — cap +5%"),
            make_rule_outcome("RULE-010", triggered=True, reason="Coureur débutant — cap +5%"),
            make_rule_outcome("RULE-016", triggered=True, reason="Débutant + chronic_load < 25 km"),
        ],
    )


@pytest.fixture
def memory_store(tmp_path):
    store = MemoryStore(memory_dir=tmp_path)
    store.add_decision(_past_decision())
    return store


@pytest.fixture
def context_retriever(memory_store):
    vs = build_runner_context_store(_RUNNER_ID, memory_store)
    return RunnerContextRetriever(store=vs)


@pytest.fixture
def interpreted():
    return EnvelopeInterpreter().interpret(_similar_envelope())


# ── retrieval ────────────────────────────────────────────────────────────────

def test_retriever_returns_snippet_for_similar_context(context_retriever, interpreted):
    snippets = context_retriever.retrieve(_RUNNER_ID, interpreted)
    assert len(snippets) >= 1


def test_retrieved_snippet_has_positive_similarity(context_retriever, interpreted):
    snippets = context_retriever.retrieve(_RUNNER_ID, interpreted)
    assert snippets[0].similarity_score > 0.0


def test_actual_outcome_appears_in_snippet_observation(context_retriever, interpreted):
    snippets = context_retriever.retrieve(_RUNNER_ID, interpreted)
    observations = " ".join(s.observation for s in snippets)
    assert "douleur genou" in observations


def test_no_snippets_for_different_runner(memory_store, interpreted):
    vs = build_runner_context_store("other-runner", memory_store)
    retriever = RunnerContextRetriever(store=vs)
    snippets = retriever.retrieve("other-runner", interpreted)
    assert snippets == []


def test_unrelated_query_scores_lower(memory_store):
    vs = build_runner_context_store(_RUNNER_ID, memory_store)
    retriever = RunnerContextRetriever(store=vs)

    # similar query
    similar_env = _similar_envelope()
    similar_interp = EnvelopeInterpreter().interpret(similar_env)
    similar_snippets = retriever.retrieve(_RUNNER_ID, similar_interp)

    # unrelated query (different action, no matching rules)
    unrelated_env = make_envelope(
        action="rest",
        triggered_rules=[make_rule_outcome("RULE-001", triggered=True, reason="Douleur critique")],
    )
    unrelated_interp = EnvelopeInterpreter().interpret(unrelated_env)
    unrelated_snippets = retriever.retrieve(_RUNNER_ID, unrelated_interp)

    similar_score = similar_snippets[0].similarity_score if similar_snippets else 0.0
    unrelated_score = unrelated_snippets[0].similarity_score if unrelated_snippets else 0.0
    assert similar_score > unrelated_score


# ── reasoning context ─────────────────────────────────────────────────────────

def test_memory_flows_into_reasoning_context(context_retriever, interpreted):
    snap = make_snapshot()
    state = make_state(runner_id=_RUNNER_ID)
    pers = RunnerPersonalizer().personalize(snap, state.profile, state.context)
    memory_snippets = context_retriever.retrieve(_RUNNER_ID, interpreted)
    context = ReasoningContextBuilder().build(interpreted, pers, [], memory_snippets)
    assert len(context.memory_snippets) >= 1


# ── prompt ────────────────────────────────────────────────────────────────────

def test_memory_section_appears_in_prompt(context_retriever, interpreted):
    snap = make_snapshot()
    state = make_state(runner_id=_RUNNER_ID)
    pers = RunnerPersonalizer().personalize(snap, state.profile, state.context)
    memory_snippets = context_retriever.retrieve(_RUNNER_ID, interpreted)
    context = ReasoningContextBuilder().build(interpreted, pers, [], memory_snippets)
    prompt = build_prompt(context)
    assert "MÉMOIRE COUREUR" in prompt


def test_outcome_text_appears_in_prompt(context_retriever, interpreted):
    snap = make_snapshot()
    state = make_state(runner_id=_RUNNER_ID)
    pers = RunnerPersonalizer().personalize(snap, state.profile, state.context)
    memory_snippets = context_retriever.retrieve(_RUNNER_ID, interpreted)
    context = ReasoningContextBuilder().build(interpreted, pers, [], memory_snippets)
    prompt = build_prompt(context)
    assert "douleur genou" in prompt


def test_no_memory_section_when_store_empty(interpreted):
    retriever = RunnerContextRetriever(store=None)
    snap = make_snapshot()
    state = make_state(runner_id=_RUNNER_ID)
    pers = RunnerPersonalizer().personalize(snap, state.profile, state.context)
    memory_snippets = retriever.retrieve(_RUNNER_ID, interpreted)
    context = ReasoningContextBuilder().build(interpreted, pers, [], memory_snippets)
    prompt = build_prompt(context)
    assert "MÉMOIRE COUREUR" not in prompt


# ── full pipeline (stub LLM) ──────────────────────────────────────────────────

def test_full_loop_memory_reaches_llm_user_prompt(context_retriever):
    """The LLM's user_prompt must contain MÉMOIRE COUREUR with the outcome text."""
    env = _similar_envelope()
    snap = make_snapshot(experience="beginner")
    state = make_state(runner_id=_RUNNER_ID, experience="beginner")
    stub = StubLLMClient()

    build_coach_response(
        env, snap, state,
        llm_client=stub,
        context_retriever=context_retriever,
    )

    assert len(stub.calls) == 1
    _system_prompt, user_prompt = stub.calls[0]
    assert "MÉMOIRE COUREUR" in user_prompt
    assert "douleur genou" in user_prompt


def test_full_loop_without_memory_has_no_memory_section():
    """Without memory, the LLM prompt must not contain a MÉMOIRE COUREUR section."""
    env = _similar_envelope()
    snap = make_snapshot()
    state = make_state(runner_id=_RUNNER_ID)
    stub = StubLLMClient()

    build_coach_response(
        env, snap, state,
        llm_client=stub,
        context_retriever=RunnerContextRetriever(store=None),
    )

    _system_prompt, user_prompt = stub.calls[0]
    assert "MÉMOIRE COUREUR" not in user_prompt
