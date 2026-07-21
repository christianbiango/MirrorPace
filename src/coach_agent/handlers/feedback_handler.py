"""Collect user feedback linked to the last coaching decision.

V1: acknowledge + persist FeedbackEntry to feedback.yaml.
The decision_ref links the feedback to the KE decision that generated it (D-013).
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from src.coach_agent.domain.feedback import FeedbackEntry
from src.coach_agent.domain.session import ConversationSession
from src.coach_agent.session.feedback_store import FeedbackStore

_ACK_WITH_DECISION = (
    "Noté. Je conserve ton retour lié à la recommandation de cette semaine. "
    "Ces informations m'aideront à mieux calibrer les prochaines analyses."
)
_ACK_WITHOUT_DECISION = (
    "Noté. Lance d'abord \"analyse ma semaine\" pour que je puisse lier ton retour "
    "à une décision de coaching."
)


class FeedbackHandler:
    def __init__(self, feedback_store: FeedbackStore) -> None:
        self._store = feedback_store

    def handle(
        self,
        user_message: str,
        session: ConversationSession,
        runner_id: str,
    ) -> tuple[str, FeedbackEntry | None]:
        """Return (ack_text, stored_entry). Entry is None if nothing was persisted."""
        decision_ref: str | None = None
        if session.last_decision_record is not None:
            decision_ref = session.last_decision_record.decision_ref

        timestamp = datetime.now(tz=timezone.utc).isoformat()
        entry_id = _hash(f"{runner_id}:{decision_ref or 'none'}:{timestamp}")

        entry = FeedbackEntry(
            id=entry_id,
            runner_id=runner_id,
            decision_ref=decision_ref,
            session_id=session.session_id,
            text=user_message,
            timestamp=timestamp,
        )
        self._store.add(entry)

        ack = _ACK_WITH_DECISION if decision_ref else _ACK_WITHOUT_DECISION
        return ack, entry


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:12]
