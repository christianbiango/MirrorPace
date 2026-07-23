"""Answer follow-up questions using session context + memory retrieval.

Uses the DecisionEnvelope (deterministic facts) and previous CoachResponse
(already generated text) to ground the follow-up LLM call.
Never re-runs the Knowledge Engine — facts come from session state.
"""

from __future__ import annotations

import json

from src.coach_agent.domain.session import ConversationSession
from src.coach_intelligence.assembler.response_assembler import LLMClient
from src.runner_memory.indexer import build_runner_context_store
from src.runner_memory.store import MemoryStore

_FOLLOWUP_SYSTEM = (
    "Tu es un coach de course à pied expert. "
    "Tu réponds à des questions de suivi sur une décision de coaching que tu as déjà prise.\n\n"
    "RÈGLES ABSOLUES :\n"
    "- Ne jamais inventer de métriques. Toutes les données sont dans le contexte fourni.\n"
    "- La décision du système (action, cible km) est basée sur les données d'activité récente enregistrées — ne la contredis pas.\n"
    "- Si le coureur signale que ses informations biographiques (expérience, âge, historique) ne correspondent pas, "
    "reconnais-le honnêtement : explique que le système se base sur la charge d'activité récente enregistrée, "
    "pas sur l'expérience biographique déclarée. Suggère de mettre à jour le profil si nécessaire.\n"
    "- Utilise les règles déclenchées et les métriques du contexte pour justifier ta réponse.\n"
    "- Reste dans le rôle d'un coach, pas d'un assistant générique.\n"
    "- Réponses directes et utiles (3-5 phrases).\n\n"
    'Réponds en JSON : {"text": "<ta réponse>"}'
)

_NO_ANALYSIS_TEXT = (
    "Je n'ai pas encore analysé ta semaine. "
    "Dis-moi \"analyse ma semaine\" pour commencer."
)


class FollowupHandler:
    def __init__(self, llm_client: LLMClient, memory_store: MemoryStore) -> None:
        self._llm = llm_client
        self._memory_store = memory_store

    def handle(
        self,
        user_message: str,
        session: ConversationSession,
    ) -> tuple[str, list[str]]:
        """Return (response_text, memory_snippets_used)."""
        if session.last_envelope is None:
            return _NO_ANALYSIS_TEXT, []

        memory_snippets = self._retrieve_memory(user_message, session)
        prompt = _build_prompt(user_message, session, memory_snippets)
        raw = self._llm.generate(_FOLLOWUP_SYSTEM, prompt)

        try:
            data = json.loads(raw.text)
            text = data.get("text", raw.text)
        except (json.JSONDecodeError, AttributeError):
            text = raw.text

        return text, memory_snippets

    def _retrieve_memory(
        self,
        query: str,
        session: ConversationSession,
    ) -> list[str]:
        if session.last_state is None:
            return []
        runner_id = session.last_state.meta.runner_id
        try:
            context_store = build_runner_context_store(runner_id, self._memory_store)
            if len(context_store) == 0:
                return []
            results = context_store.query(query, k=3)
            return [doc.get("observation", "") for _, _, doc in results if doc.get("observation")]
        except Exception:
            return []


def _build_prompt(
    user_message: str,
    session: ConversationSession,
    memory_snippets: list[str],
) -> str:
    parts: list[str] = []

    envelope = session.last_envelope
    if envelope:
        triggered = [r for r in envelope.triggered_rules if r.triggered]
        rules_str = "; ".join(
            f"{r.rule_id}: {r.reason}" for r in triggered
        ) or "aucune règle déclenchée"
        parts.append(
            "DÉCISION SYSTÈME :\n"
            f"- Action : {envelope.decision.action}\n"
            f"- Cible semaine prochaine : {envelope.decision.absolute_next_week_target_km:.1f} km\n"
            f"- Readiness : {envelope.readiness.score}/100\n"
            f"- Règles déclenchées : {rules_str}"
        )

    response = session.last_coach_response
    if response:
        parts.append(
            "RÉPONSE PRÉCÉDENTE DU COACH :\n"
            f"{response.decision_summary}\n"
            f"{response.main_message}"
        )

    if memory_snippets:
        snippets_str = "\n".join(f"- {s}" for s in memory_snippets)
        parts.append(f"CONTEXTE MÉMOIRE :\n{snippets_str}")

    history = session.turns[-6:]
    if history:
        history_str = "\n".join(f"{t.role}: {t.text}" for t in history)
        parts.append(f"HISTORIQUE DE CONVERSATION :\n{history_str}")

    parts.append(f"Question : {user_message}")
    return "\n\n".join(parts)
