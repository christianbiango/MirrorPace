from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RawLLMResponse:
    text: str
    model: str
    input_tokens: int
    output_tokens: int


@dataclass
class CoachResponse:
    decision_summary: str
    main_message: str
    scientific_context: list[str] = field(default_factory=list)
    personal_context: list[str] = field(default_factory=list)
    plan_hints_formatted: list[str] = field(default_factory=list)
    medical_alert: str | None = None
    confidence_note: str | None = None
    response_ref: str = ""
    envelope_ref: str = ""
