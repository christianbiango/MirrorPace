"""Hybrid intent classifier: deterministic patterns first, LLM fallback on ambiguity.

First pass: regex patterns on normalised text.
  - Exactly one category matches → return it, high confidence, method="pattern".
  - Zero or multiple categories match → LLM fallback (or GENERAL_QUESTION if no LLM).

LLM fallback: single lightweight call asking for {"intent": "<CATEGORY>"}.
"""

from __future__ import annotations

import json
import re
import unicodedata

from src.coach_agent.domain.intent import IntentClassification, UserIntent
from src.coach_agent.domain.session import ConversationTurn
from src.coach_intelligence.assembler.response_assembler import LLMClient

# --- Pattern registry --------------------------------------------------------

_PATTERNS: dict[UserIntent, list[str]] = {
    UserIntent.ANALYSIS_REQUEST: [
        r"\banalyse?\b",
        r"\banalyser\b",
        r"\brecommandes?\b",
        r"\brecommandation\b",
        r"\bbilan\b",
        r"\bevaluation?\b",
        r"\bcheck\b",
        r"\bque faire\b",
        r"\bquoi faire\b",
        r"\bma semaine\b",
    ],
    UserIntent.EXPLANATION_REQUEST: [
        r"\bpourquoi\b",
        r"\bexplique\b",
        r"\bexpliques\b",
        r"\bclarif\b",
        r"\bpas compris\b",
        r"\bveut dire\b",
        r"\bsignifie\b",
        r"\bc.est quoi\b",
        r"\bje ne comprends pas\b",
        r"\bje comprends pas\b",
    ],
    UserIntent.HYPOTHETICAL: [
        r"\bet si\b",
        r"\bque se passe.t.il\b",
        r"\bque.*passerait.il\b",
        r"\bsi j.augment\b",
        r"\bsi je cour\b",
        r"\bsi je fai\b",
        r"\bsi je refai\b",
        r"\bscenario\b",
    ],
    UserIntent.FEEDBACK: [
        r"\bc.etait\b",
        r"\bj.ai (eu|ressenti|vecu)\b",
        r"\btrop (facile|difficile|dur)\b",
        r"\bdouleur\b",
        r"\bmal (au|a|aux)\b",
        r"\bblessure\b",
        r"\bbless[ei]\b",
        r"\bfatigue\b",
        r"\bepuise\b",
        r"\bj.ai fait.*km\b",
        r"\bfinalement.*km\b",
        r"\bmauvaise semaine\b",
    ],
}

_CLASSIFY_SYSTEM = (
    "Classifie le message utilisateur dans exactement une de ces catégories :\n"
    "- ANALYSIS_REQUEST : demande d'analyse ou recommandation sur l'entraînement\n"
    "- EXPLANATION_REQUEST : demande d'explication sur une décision de coaching\n"
    "- HYPOTHETICAL : exploration d'un scénario hypothétique\n"
    "- FEEDBACK : retour sur une expérience vécue ou ressenti physique\n"
    "- GENERAL_QUESTION : autre question générale\n\n"
    'Réponds en JSON : {"intent": "<CATEGORIE>"}'
)


def _normalize(text: str) -> str:
    """Lowercase + strip accents for robust matching."""
    nfd = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


class IntentClassifier:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client

    def classify(
        self,
        message: str,
        recent_turns: list[ConversationTurn] | None = None,
    ) -> IntentClassification:
        result = self._classify_by_pattern(message)
        if result is not None:
            return result
        if self._llm is not None:
            return self._classify_by_llm(message, recent_turns or [])
        return IntentClassification(
            intent=UserIntent.GENERAL_QUESTION,
            confidence="low",
            method="pattern",
        )

    # ── pattern pass ──────────────────────────────────────────────────────────

    def _classify_by_pattern(self, message: str) -> IntentClassification | None:
        normalized = _normalize(message)
        matches: dict[UserIntent, int] = {}
        for intent, patterns in _PATTERNS.items():
            count = sum(1 for p in patterns if re.search(p, normalized))
            if count > 0:
                matches[intent] = count
        if len(matches) == 1:
            intent = next(iter(matches))
            return IntentClassification(intent=intent, confidence="high", method="pattern")
        return None  # ambiguous or no match → LLM fallback

    # ── LLM fallback ──────────────────────────────────────────────────────────

    def _classify_by_llm(
        self,
        message: str,
        recent_turns: list[ConversationTurn],
    ) -> IntentClassification:
        context = ""
        if recent_turns:
            lines = "\n".join(f"{t.role}: {t.text}" for t in recent_turns[-3:])
            context = f"Contexte récent:\n{lines}\n\n"
        user_prompt = f"{context}Message: {message}"

        raw = self._llm.generate(_CLASSIFY_SYSTEM, user_prompt)
        try:
            data = json.loads(raw.text)
            intent = UserIntent(data["intent"])
        except (json.JSONDecodeError, KeyError, ValueError):
            intent = UserIntent.GENERAL_QUESTION

        return IntentClassification(intent=intent, confidence="high", method="llm")
