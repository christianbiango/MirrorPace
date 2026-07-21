from __future__ import annotations

from datetime import datetime, timezone

from src.coach_agent.domain.session import ConversationSession


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, ConversationSession] = {}

    def get_or_create(self, session_id: str) -> ConversationSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationSession(
                session_id=session_id,
                created_at=datetime.now(tz=timezone.utc).isoformat(),
            )
        return self._sessions[session_id]

    def save(self, session: ConversationSession) -> None:
        self._sessions[session.session_id] = session
