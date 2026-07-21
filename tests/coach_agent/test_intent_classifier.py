"""Unit tests for IntentClassifier — pattern pass only (no LLM needed)."""

from __future__ import annotations

import pytest

from src.coach_agent.domain.intent import UserIntent
from src.coach_agent.intent.classifier import IntentClassifier

_clf = IntentClassifier(llm_client=None)


# ── ANALYSIS_REQUEST ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("message", [
    "Analyse ma semaine",
    "Qu'est-ce que tu recommandes ?",
    "Fais un bilan de ma semaine",
    "Check ma semaine",
    "Que faire cette semaine ?",
])
def test_analysis_patterns(message):
    result = _clf.classify(message)
    assert result.intent == UserIntent.ANALYSIS_REQUEST
    assert result.method == "pattern"
    assert result.confidence == "high"


# ── EXPLANATION_REQUEST ───────────────────────────────────────────────────────

@pytest.mark.parametrize("message", [
    "Pourquoi tu me demandes de réduire ?",
    "Explique-moi cette décision",
    "Je ne comprends pas pourquoi",
    "C'est quoi le ACWR ?",
    "Je comprends pas",
])
def test_explanation_patterns(message):
    result = _clf.classify(message)
    assert result.intent == UserIntent.EXPLANATION_REQUEST
    assert result.method == "pattern"


# ── HYPOTHETICAL ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("message", [
    "Et si j'augmentais quand même ?",
    "Et si je courais 60km cette semaine ?",
    "Si j'augmente de 10%, que se passe-t-il ?",
    "Scénario : je fais quand même 50km",
])
def test_hypothetical_patterns(message):
    result = _clf.classify(message)
    assert result.intent == UserIntent.HYPOTHETICAL
    assert result.method == "pattern"


# ── FEEDBACK ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("message", [
    "C'était trop difficile cette semaine",
    "J'ai eu une douleur au genou",
    "J'ai fait finalement 42km",
    "Blessure au mollet depuis mardi",
    "Je suis épuisé",
])
def test_feedback_patterns(message):
    result = _clf.classify(message)
    assert result.intent == UserIntent.FEEDBACK
    assert result.method == "pattern"


# ── FALLBACK (no LLM) ─────────────────────────────────────────────────────────

def test_ambiguous_falls_back_to_general_without_llm():
    # "Pourquoi analyser maintenant ?" matches both EXPLANATION and ANALYSIS
    # With no LLM, should fall back to GENERAL_QUESTION with low confidence
    result = _clf.classify("Pourquoi analyser maintenant ?")
    assert result.intent == UserIntent.GENERAL_QUESTION
    assert result.confidence == "low"


def test_unknown_message_falls_back_to_general():
    result = _clf.classify("Bonjour comment ça va")
    assert result.intent == UserIntent.GENERAL_QUESTION


# ── normalisation (accents) ────────────────────────────────────────────────────

def test_accents_are_normalized():
    result = _clf.classify("Évaluation de ma semaine s'il te plaît")
    assert result.intent == UserIntent.ANALYSIS_REQUEST
