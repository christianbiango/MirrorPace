from __future__ import annotations

import pytest

from src.coach_intelligence.assembler.prompt_builder import build_prompt
from src.coach_intelligence.interpreter.envelope_interpreter import EnvelopeInterpreter
from src.coach_intelligence.personalizer.runner_personalizer import RunnerPersonalizer
from src.coach_intelligence.reasoning.context_builder import ReasoningContextBuilder
from src.coach_intelligence.domain.schemas.rag_results import ScientificSnippet, MemorySnippet
from src.knowledge_engine.api import PlanHint
from tests.coach_intelligence.conftest import make_envelope, make_snapshot, make_state, make_rule_outcome


def _build_context(
    medical: bool = False,
    medical_reason: str | None = None,
    plan_hints: list | None = None,
    sci_snippets: list | None = None,
    mem_snippets: list | None = None,
):
    env = make_envelope(medical=medical, medical_reason=medical_reason, plan_hints=plan_hints)
    snap = make_snapshot()
    state = make_state()
    interp = EnvelopeInterpreter().interpret(env)
    pers = RunnerPersonalizer().personalize(snap, state.profile, state.context)
    return ReasoningContextBuilder().build(
        interp, pers,
        sci_snippets or [],
        mem_snippets or [],
    )


def test_medical_alert_in_prompt_when_flagged():
    ctx = _build_context(medical=True, medical_reason="pain_critical")
    prompt = build_prompt(ctx)
    assert "ALERTE MÉDICALE" in prompt


def test_no_medical_section_when_no_flag():
    ctx = _build_context(medical=False)
    prompt = build_prompt(ctx)
    assert "ALERTE MÉDICALE" not in prompt


def test_readiness_score_in_prompt():
    ctx = _build_context()
    prompt = build_prompt(ctx)
    assert "70" in prompt  # readiness_score from make_envelope fixture


def test_scientific_snippets_in_prompt():
    sci = [ScientificSnippet(rule_id="RULE-003", source="Gabbett 2016", claim="ACWR > 1.5 risky", explanation="...", relevance=0.9)]
    ctx = _build_context(sci_snippets=sci)
    prompt = build_prompt(ctx)
    assert "Gabbett 2016" in prompt


def test_no_scientific_section_when_empty():
    ctx = _build_context(sci_snippets=[])
    prompt = build_prompt(ctx)
    assert "CONTEXTE SCIENTIFIQUE" not in prompt


def test_memory_snippets_in_prompt():
    mem = [MemorySnippet(type="pattern", reference_period="last week", observation="Observation clé", relevance_note="note", similarity_score=0.8)]
    ctx = _build_context(mem_snippets=mem)
    prompt = build_prompt(ctx)
    assert "Observation clé" in prompt


def test_no_memory_section_when_empty():
    ctx = _build_context(mem_snippets=[])
    prompt = build_prompt(ctx)
    assert "MÉMOIRE COUREUR" not in prompt


def test_plan_hints_in_prompt():
    hints = [PlanHint(rule_id="RULE-015", hint="structure_macroplan")]
    ctx = _build_context(plan_hints=hints)
    prompt = build_prompt(ctx)
    assert "structure_macroplan" in prompt


def test_no_plan_hints_section_when_empty():
    ctx = _build_context(plan_hints=[])
    prompt = build_prompt(ctx)
    assert "CONSEILS DE PLANIFICATION" not in prompt


def test_profile_section_present():
    ctx = _build_context()
    prompt = build_prompt(ctx)
    assert "PROFIL COUREUR" in prompt


def test_decision_section_present():
    ctx = _build_context()
    prompt = build_prompt(ctx)
    assert "DÉCISION" in prompt
