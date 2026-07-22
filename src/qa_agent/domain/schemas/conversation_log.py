from __future__ import annotations

from dataclasses import dataclass, field

from src.coach_agent.domain.intent import AgentResponse
from src.knowledge_engine.domain.schemas.decision import DecisionEnvelope
from src.qa_agent.domain.schemas.runner_profile import RunnerProfile


@dataclass
class ConversationEntry:
    turn_number: int
    user_message: str
    agent_response: AgentResponse
    envelope_snapshot: DecisionEnvelope | None = None


@dataclass
class ConversationLog:
    conversation_id: str
    runner_profile: RunnerProfile
    entries: list[ConversationEntry]
    termination_reason: str  # "satisfied" | "max_turns" | "error"
    started_at: str
    ended_at: str
    runner_id: str | None = None
