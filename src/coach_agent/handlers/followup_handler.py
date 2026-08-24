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
from src.runner_model.profile_store import RunnerProfileStore

_VALID_EXPERIENCE_LEVELS = {"beginner", "intermediate", "advanced"}

_FOLLOWUP_SYSTEM = (
    "Tu es un coach de course à pied expert. "
    "Tu réponds à des questions de suivi sur une décision de coaching que tu as déjà prise.\n\n"
    "RÈGLES ABSOLUES :\n"
    "- Ne jamais inventer de métriques. Toutes les données sont dans le contexte fourni.\n"
    "- La décision du système (action, cible km) est basée sur les données d'activité récente enregistrées — ne la contredis pas.\n"
    "- Le contexte DÉCISION SYSTÈME contient experience_level_source (declared|calculated|reconciled) : "
    "si le coureur signale que ses informations biographiques ne correspondent pas, cite la vraie raison. "
    "Si source=calculated : sa charge d'activité récente ne confirme pas encore le niveau qu'il a déclaré, "
    "donc tu restes prudent malgré sa déclaration. Si source=declared : tu respectes son niveau déclaré même "
    "si sa charge récente permettrait davantage. Si source=reconciled : il n'y a pas de discordance.\n"
    "- Si le coureur déclare une information qui diffère du PROFIL ENREGISTRÉ fourni dans le contexte "
    "(nombre d'années de course, niveau d'expérience), termine ta réponse par une question de confirmation "
    "explicite avant toute mise à jour, par exemple : \"Je note que tu cours depuis 8 ans — je mets à jour "
    "ton profil ?\". Renseigne alors le champ profile_correction avec UNIQUEMENT les champs qui diffèrent.\n"
    "- Ne renseigne profile_correction que si le coureur affirme un fait sur lui-même, jamais pour une "
    "question ou une hypothèse.\n"
    "- Utilise les règles déclenchées et les métriques du contexte pour justifier ta réponse.\n"
    "- Reste dans le rôle d'un coach, pas d'un assistant générique.\n"
    "- Réponses directes et utiles (3-5 phrases).\n\n"
    'Réponds en JSON : {"text": "<ta réponse>", "profile_correction": '
    '{"years_running": <float|null>, "experience_level_declared": "<beginner|intermediate|advanced>"} ou null}'
)

_NO_ANALYSIS_TEXT = (
    "Je n'ai pas encore analysé ta semaine. "
    "Dis-moi \"analyse ma semaine\" pour commencer."
)


class FollowupHandler:
    def __init__(
        self,
        llm_client: LLMClient,
        memory_store: MemoryStore,
        profile_store: RunnerProfileStore | None = None,
    ) -> None:
        self._llm = llm_client
        self._memory_store = memory_store
        self._profile_store = profile_store

    def handle(
        self,
        user_message: str,
        session: ConversationSession,
    ) -> tuple[str, list[str], dict | None]:
        """Return (response_text, memory_snippets_used, profile_correction_candidate)."""
        if session.last_envelope is None:
            return _NO_ANALYSIS_TEXT, [], None

        current_profile = self._load_current_profile()
        memory_snippets = self._retrieve_memory(user_message, session)
        prompt = _build_prompt(user_message, session, memory_snippets, current_profile)
        raw = self._llm.generate(_FOLLOWUP_SYSTEM, prompt)

        try:
            data = json.loads(raw.text)
            text = data.get("text", raw.text)
            correction = _validate_correction(data.get("profile_correction"), current_profile)
        except (json.JSONDecodeError, AttributeError):
            text = raw.text
            correction = None

        return text, memory_snippets, correction

    def _load_current_profile(self):
        if self._profile_store is None:
            return None
        try:
            _, profile = self._profile_store.load()
            return profile
        except Exception:
            return None

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


def _validate_correction(candidate, current_profile) -> dict | None:
    """Keep only fields that are well-formed AND differ from the stored profile."""
    if not isinstance(candidate, dict) or current_profile is None:
        return None

    result: dict = {}

    years_running = candidate.get("years_running")
    if isinstance(years_running, (int, float)) and years_running != current_profile.years_running:
        result["years_running"] = float(years_running)

    experience_level = candidate.get("experience_level_declared")
    if (
        isinstance(experience_level, str)
        and experience_level in _VALID_EXPERIENCE_LEVELS
        and experience_level != current_profile.experience_level_declared
    ):
        result["experience_level_declared"] = experience_level

    return result or None


def _build_prompt(
    user_message: str,
    session: ConversationSession,
    memory_snippets: list[str],
    current_profile,
) -> str:
    parts: list[str] = []

    if current_profile is not None:
        parts.append(
            "PROFIL ENREGISTRÉ :\n"
            f"- Années de course déclarées : {current_profile.years_running if current_profile.years_running is not None else 'inconnu'}\n"
            f"- Niveau d'expérience déclaré : {current_profile.experience_level_declared}"
        )

    envelope = session.last_envelope
    if envelope:
        triggered = [r for r in envelope.triggered_rules if r.triggered]
        rules_str = "; ".join(r.reason for r in triggered if r.reason) or "aucune règle déclenchée"
        parts.append(
            "DÉCISION SYSTÈME :\n"
            f"- Action : {envelope.decision.action}\n"
            f"- Cible semaine prochaine : {envelope.decision.absolute_next_week_target_km:.1f} km\n"
            f"- Readiness : {envelope.readiness.score}/100\n"
            f"- Règles déclenchées : {rules_str}\n"
            f"- Niveau d'expérience retenu : {envelope.experience_level} "
            f"(experience_level_source: {envelope.experience_level_source})"
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
