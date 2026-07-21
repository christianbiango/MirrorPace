"""Shared rule primitives — RuleContext and helpers.

Every rule is a pure function: (RunnerState, ComputedVariables, Config) → RuleOutcome.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ..config.loader import EngineConfig
from ..domain.schemas.computed import ComputedVariables
from ..domain.schemas.rule_outcome import RuleOutcome
from ..domain.schemas.runner_state import RunnerState

RuleFn = Callable[[RunnerState, ComputedVariables, EngineConfig], RuleOutcome]


@dataclass(frozen=True)
class RuleSpec:
    rule_id: str
    priority: str  # P0..P4
    fn: RuleFn


def not_triggered(rule_id: str, priority: str) -> RuleOutcome:
    return RuleOutcome(rule_id=rule_id, priority=priority, triggered=False, action=None)


def snapshot(**kwargs: Any) -> dict[str, Any]:
    """Convenience helper — filter out None values from a variables_snapshot dict."""
    return {k: v for k, v in kwargs.items() if v is not None}
