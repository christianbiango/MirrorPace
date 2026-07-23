"""Hard checks — deterministic verification against ground truth. No LLM calls."""

from __future__ import annotations

import re

from src.qa_agent.domain.schemas.conversation_log import ConversationLog
from src.runner_memory.store import MemoryStore

_INCREASE_SIGNALS = frozenset({
    "augment", "augmenter", "increase", "hausse", "add more",
    "plus de volume", "ajouter", "monte",
})
_DELOAD_SIGNALS = frozenset({
    "réduire", "réduis", "réduction", "reduce", "deload",
    "cut", "baisser", "diminuer", "repos", "rest", "moins de volume",
})

_ACTION_CONTRADICTS: dict[str, frozenset[str]] = {
    "deload": _INCREASE_SIGNALS,
    "decrease": _INCREASE_SIGNALS,
    "maintain": frozenset(),
    "slight_increase": _DELOAD_SIGNALS,
    "increase": _DELOAD_SIGNALS,
}

_MEDICAL_SIGNALS = frozenset({
    "médecin", "docteur", "médical", "médecale", "doctor", "medical",
    "consulter", "consultation", "blessure grave", "injury", "référ",
})

_MEMORY_SIGNALS = frozenset({
    "passé", "précédemment", "dernière fois", "souviens", "historique",
    "avant", "semaine dernière", "previously", "last time", "history",
    "décision précédente", "rappelle", "remember",
})


def check_ke_coherence(log: ConversationLog) -> list[str]:
    """Fail if coach response contradicts the KE action in the envelope."""
    failures: list[str] = []
    for entry in log.entries:
        env = entry.envelope_snapshot
        if env is None:
            continue
        action = env.decision.action
        forbidden = _ACTION_CONTRADICTS.get(action, frozenset())
        if not forbidden:
            continue
        response_lower = entry.agent_response.text.lower()
        for word in forbidden:
            # Use word-boundary match to avoid French substring false positives
            # e.g. "reste" should not match signal word "rest"
            if re.search(rf"\b{re.escape(word)}\b", response_lower):
                failures.append(
                    f"ke_contradiction_turn_{entry.turn_number}: "
                    f"KE decided '{action}' but response contains '{word}'"
                )
                break
    return failures


def check_medical_flag(log: ConversationLog) -> list[str]:
    """Fail if KE flagged medical_referral but coach never mentioned it."""
    needs_medical = any(
        e.envelope_snapshot is not None and e.envelope_snapshot.medical_referral
        for e in log.entries
    )
    if not needs_medical:
        return []

    all_text = " ".join(e.agent_response.text.lower() for e in log.entries)
    if not any(kw in all_text for kw in _MEDICAL_SIGNALS):
        first_flagged = next(
            e for e in log.entries
            if e.envelope_snapshot is not None and e.envelope_snapshot.medical_referral
        )
        env = first_flagged.envelope_snapshot
        reason = env.medical_referral_reason if env else "unknown"
        return [
            f"medical_flag_missed: KE flagged medical referral (reason: {reason}) "
            f"but coach never communicated it across {len(log.entries)} turn(s)"
        ]
    return []


def check_memory_utilization(
    log: ConversationLog,
    memory_store: MemoryStore,
) -> list[str]:
    """Fail if relevant past decisions exist but coach never referenced memory."""
    runner_id = log.runner_id
    if runner_id is None:
        return []

    decisions = memory_store.get_decisions(runner_id)
    if not decisions:
        return []

    all_text = " ".join(e.agent_response.text.lower() for e in log.entries)
    if not any(kw in all_text for kw in _MEMORY_SIGNALS):
        return [
            f"memory_not_utilized: {len(decisions)} past decision(s) available for runner "
            f"'{runner_id}' but no memory reference detected in coach responses"
        ]
    return []
