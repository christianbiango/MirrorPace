"""Public re-exports for convenience — one-line import for callers."""

from __future__ import annotations

from .config.loader import EngineConfig, load_default_config
from .domain.schemas.computed import ComputedVariables, ReadinessComponentScores
from .domain.schemas.decision import (
    Decision,
    DecisionEnvelope,
    DecisionMeta,
    LlmContext,
    PlanHint,
    ReadinessOut,
)
from .domain.schemas.rule_outcome import RuleOutcome
from .domain.schemas.runner_state import (
    PainRegion,
    PlanContext,
    RunnerProfile,
    RunnerState,
    RunnerStateMeta,
    WeekInput,
)
from .engine.orchestrator import run_engine
from .engine.validator import ValidationError, ValidationReport, validate

__all__ = [
    "ComputedVariables",
    "Decision",
    "DecisionEnvelope",
    "DecisionMeta",
    "EngineConfig",
    "LlmContext",
    "PainRegion",
    "PlanContext",
    "PlanHint",
    "ReadinessComponentScores",
    "ReadinessOut",
    "RuleOutcome",
    "RunnerProfile",
    "RunnerState",
    "RunnerStateMeta",
    "ValidationError",
    "ValidationReport",
    "WeekInput",
    "load_default_config",
    "run_engine",
    "validate",
]
