from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AggregateReport:
    total_conversations: int
    mean_global_score: float
    std_global_score: float
    scores_by_dimension: dict[str, float]
    memory_utilization_rate: float
    ke_contradiction_rate: float
    medical_flag_miss_rate: float
    termination_breakdown: dict[str, int]
    top_blockers: list[tuple[str, int]]
    interesting_conversations: list[str]
    generated_at: str
