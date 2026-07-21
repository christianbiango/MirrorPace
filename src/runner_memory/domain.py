"""Runner Memory domain objects.

Two entity types:
- CoachingDecision : one entry per pipeline run, captures the KE decision + context
- RunnerEvent      : manually entered facts (injury, illness, race, rest period)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

EventType = Literal["injury", "illness", "race", "rest_period", "high_load_block"]
Severity = Literal["mild", "moderate", "severe"]


@dataclass
class CoachingDecision:
    id: str                           # sha256[:12] of runner_id+week_start+action
    runner_id: str
    date: str                         # ISO-8601 date of pipeline run
    week_start: str                   # Monday of the analysed week (ISO-8601)

    # Decision context — answers "why was this taken?" months later
    decision_ref: str                 # sha256[:12] of envelope computed_at+action+readiness
    action: str                       # slight_increase | maintain | reduce_volume | …
    primary_reason: str
    dominant_rules: list[str]         # e.g. ["RULE-009", "RULE-016"]
    key_metrics_snapshot: dict        # readiness, volume, ACWR, fatigue, sleep, …

    # Outcome — filled later
    expected_outcome: str
    actual_outcome: str | None = None
    outcome_date: str | None = None

    # Pre-computed text for Jaccard indexing
    text: str = ""


@dataclass
class RunnerEvent:
    id: str                           # sha256[:12] of runner_id+date+event_type
    runner_id: str
    date: str                         # ISO-8601 date event started
    event_type: EventType
    description: str

    body_part: str | None = None      # for injury/pain entries
    severity: Severity | None = None
    resolved_date: str | None = None
    notes: str = ""

    # Pre-computed text for Jaccard indexing
    text: str = ""
