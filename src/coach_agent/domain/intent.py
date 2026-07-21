from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from src.coach_intelligence.domain.schemas.coach_response import CoachResponse


class UserIntent(str, Enum):
    ANALYSIS_REQUEST = "ANALYSIS_REQUEST"
    EXPLANATION_REQUEST = "EXPLANATION_REQUEST"
    HYPOTHETICAL = "HYPOTHETICAL"
    FEEDBACK = "FEEDBACK"
    GENERAL_QUESTION = "GENERAL_QUESTION"


@dataclass
class IntentClassification:
    intent: UserIntent
    confidence: str   # "high" | "low"
    method: str       # "pattern" | "llm"


@dataclass
class AgentResponse:
    text: str
    intent: str
    session_id: str
    turn_number: int
    coach_response: CoachResponse | None = None
    sources: list[str] = field(default_factory=list)
