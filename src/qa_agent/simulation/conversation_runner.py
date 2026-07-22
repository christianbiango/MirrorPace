"""ConversationRunner — orchestrates the SimulatedRunner ↔ CoachAgent loop."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.coach_agent.agent import CoachAgent
from src.qa_agent.domain.schemas.conversation_log import ConversationEntry, ConversationLog
from src.qa_agent.domain.schemas.runner_profile import RunnerProfile
from src.qa_agent.simulation.simulated_runner import SimulatedRunner


class ConversationRunner:
    def __init__(
        self,
        coach_agent: CoachAgent,
        api_key: str,
        max_turns: int = 5,
    ) -> None:
        self._coach = coach_agent
        self._api_key = api_key
        self._max_turns = max_turns

    def run(self, profile: RunnerProfile) -> ConversationLog:
        session_id = f"qa-{uuid.uuid4().hex[:12]}"
        runner = SimulatedRunner(profile=profile, api_key=self._api_key)

        entries: list[ConversationEntry] = []
        history: list[dict[str, str]] = []
        started_at = datetime.now(tz=timezone.utc).isoformat()
        termination_reason = "max_turns"
        runner_id: str | None = None

        first_msg = runner.first_message()
        history.append({"role": "user", "content": first_msg})

        agent_response = self._coach.ask(first_msg, session_id=session_id)
        envelope = self._extract_envelope(session_id)
        runner_id = runner_id or self._extract_runner_id(session_id)

        entries.append(ConversationEntry(
            turn_number=1,
            user_message=first_msg,
            agent_response=agent_response,
            envelope_snapshot=envelope,
        ))
        history.append({"role": "assistant", "content": agent_response.text})

        for turn in range(2, self._max_turns + 1):
            runner_msg = runner.next_message(history)

            if runner_msg.satisfied:
                termination_reason = "satisfied"
                break

            if not runner_msg.message.strip():
                termination_reason = "satisfied"
                break

            history.append({"role": "user", "content": runner_msg.message})
            agent_response = self._coach.ask(runner_msg.message, session_id=session_id)
            envelope = self._extract_envelope(session_id)

            entries.append(ConversationEntry(
                turn_number=turn,
                user_message=runner_msg.message,
                agent_response=agent_response,
                envelope_snapshot=envelope,
            ))
            history.append({"role": "assistant", "content": agent_response.text})

        return ConversationLog(
            conversation_id=session_id,
            runner_profile=profile,
            entries=entries,
            termination_reason=termination_reason,
            started_at=started_at,
            ended_at=datetime.now(tz=timezone.utc).isoformat(),
            runner_id=runner_id,
        )

    def _extract_envelope(self, session_id: str):
        """Read envelope from CoachAgent session (QA internal access — not production pattern)."""
        try:
            session = self._coach._session_store._sessions.get(session_id)
            return session.last_envelope if session else None
        except AttributeError:
            return None

    def _extract_runner_id(self, session_id: str) -> str | None:
        try:
            session = self._coach._session_store._sessions.get(session_id)
            if session and session.last_state:
                return session.last_state.meta.runner_id
        except AttributeError:
            pass
        return None
