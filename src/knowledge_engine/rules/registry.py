"""Rules registry — ordered by priority for the orchestrator."""

from __future__ import annotations

from .base import RuleSpec
from .planning_rules import PLANNING_RULES
from .progression_rules import PROGRESSION_RULES
from .race_day_rules import RACE_DAY_RULES
from .safety_rules import SAFETY_RULES

ALL_RULES: list[RuleSpec] = [
    *SAFETY_RULES,        # P0
    *PROGRESSION_RULES,   # P1, P2, P3
    *PLANNING_RULES,      # P4
    *RACE_DAY_RULES,      # P4
]

RULES_BY_PRIORITY: dict[str, list[RuleSpec]] = {
    "P0": [r for r in ALL_RULES if r.priority == "P0"],
    "P1": [r for r in ALL_RULES if r.priority == "P1"],
    "P2": [r for r in ALL_RULES if r.priority == "P2"],
    "P3": [r for r in ALL_RULES if r.priority == "P3"],
    "P4": [r for r in ALL_RULES if r.priority == "P4"],
}
