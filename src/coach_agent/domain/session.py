from __future__ import annotations

from dataclasses import dataclass, field

from src.coach_intelligence.domain.schemas.coach_response import CoachResponse
from src.knowledge_engine.api import DecisionEnvelope, RunnerState
from src.runner_memory.domain import CoachingDecision


@dataclass
class ConversationTurn:
    turn_number: int
    role: str         # "user" | "agent"
    text: str
    intent: str | None
    timestamp: str


@dataclass
class ConversationSession:
    session_id: str
    created_at: str
    turns: list[ConversationTurn] = field(default_factory=list)
    last_coach_response: CoachResponse | None = None
    last_envelope: DecisionEnvelope | None = None
    last_state: RunnerState | None = None
    last_decision_record: CoachingDecision | None = None
    pending_feedback: list[str] = field(default_factory=list)
