from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

CommunicationStyle = Literal["simple", "technical"]


@dataclass
class PersonalizationContext:
    communication_style: CommunicationStyle
    has_race_goal: bool
    weeks_to_race: int | None
    race_target_time_s: int | None
    career_context: str
    current_fitness_note: str
    intensity_profile: str | None
    relevant_pbs: dict = field(default_factory=dict)
