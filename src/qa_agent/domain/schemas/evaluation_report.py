from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DimensionScore:
    score: int
    justification: str
    cited_turn: int | None = None


@dataclass
class EvaluationReport:
    conversation_id: str
    runner_profile_id: str
    scores: dict[str, DimensionScore]
    global_score: float
    hard_check_failures: list[str]
    strengths: list[str]
    weaknesses: list[str]
    blockers: list[str]
    suggested_improvements: list[str]
    evaluated_at: str
