from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RunnerProfile:
    id: str
    display_name: str
    system_prompt: str
    opening_messages: list[str]
    expected_intents: list[str]
    tags: list[str] = field(default_factory=list)
