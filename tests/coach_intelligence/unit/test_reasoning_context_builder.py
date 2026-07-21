from __future__ import annotations

import pytest

from src.coach_intelligence.domain.schemas.rag_results import MemorySnippet, ScientificSnippet
from src.coach_intelligence.reasoning.context_builder import ReasoningContextBuilder
from tests.coach_intelligence.conftest import make_envelope, make_snapshot, make_state
from src.coach_intelligence.interpreter.envelope_interpreter import EnvelopeInterpreter
from src.coach_intelligence.personalizer.runner_personalizer import RunnerPersonalizer


def _make_sci(source: str, relevance: float) -> ScientificSnippet:
    return ScientificSnippet(
        rule_id=None, source=source, claim="claim", explanation="expl", relevance=relevance
    )


def _make_mem(score: float) -> MemorySnippet:
    return MemorySnippet(
        type="pattern",
        reference_period="last week",
        observation="obs",
        relevance_note="note",
        similarity_score=score,
    )


@pytest.fixture
def builder() -> ReasoningContextBuilder:
    return ReasoningContextBuilder(max_scientific=4, max_memory=3)


@pytest.fixture
def interpreted():
    return EnvelopeInterpreter().interpret(make_envelope())


@pytest.fixture
def personalization():
    snap = make_snapshot()
    state = make_state()
    return RunnerPersonalizer().personalize(snap, state.profile, state.context)


def test_sorts_scientific_by_relevance(builder, interpreted, personalization):
    snippets = [_make_sci("B", 0.5), _make_sci("A", 0.8), _make_sci("C", 0.1)]
    result = builder.build(interpreted, personalization, snippets, [])
    assert result.scientific_snippets[0].source == "A"
    assert result.scientific_snippets[1].source == "B"
    assert result.scientific_snippets[2].source == "C"


def test_caps_scientific_at_max(builder, interpreted, personalization):
    snippets = [_make_sci(f"Source {i}", float(i) / 10) for i in range(10)]
    result = builder.build(interpreted, personalization, snippets, [])
    assert len(result.scientific_snippets) <= 4


def test_deduplicates_by_source(builder, interpreted, personalization):
    snippets = [
        _make_sci("Same source", 0.9),
        _make_sci("Same source", 0.7),
        _make_sci("Other source", 0.5),
    ]
    result = builder.build(interpreted, personalization, snippets, [])
    sources = [s.source for s in result.scientific_snippets]
    assert sources.count("Same source") == 1


def test_caps_memory_at_max(builder, interpreted, personalization):
    memories = [_make_mem(float(i) / 10) for i in range(10)]
    result = builder.build(interpreted, personalization, [], memories)
    assert len(result.memory_snippets) <= 3


def test_memory_sorted_by_score(builder, interpreted, personalization):
    memories = [_make_mem(0.3), _make_mem(0.9), _make_mem(0.5)]
    result = builder.build(interpreted, personalization, [], memories)
    scores = [m.similarity_score for m in result.memory_snippets]
    assert scores == sorted(scores, reverse=True)


def test_token_budget_positive(builder, interpreted, personalization):
    result = builder.build(interpreted, personalization, [_make_sci("S", 0.5)], [_make_mem(0.5)])
    assert result.token_budget_used > 0


def test_empty_snippets_ok(builder, interpreted, personalization):
    result = builder.build(interpreted, personalization, [], [])
    assert result.scientific_snippets == []
    assert result.memory_snippets == []
    assert result.token_budget_used >= 0
