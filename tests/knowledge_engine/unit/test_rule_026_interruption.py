"""RULE-026 — Retour d'interruption (>N days, strict)."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.progression_rules import rule_026

from tests.knowledge_engine.fixtures.builders import make_state, with_week

CFG = load_default_config()


def _s(days):
    return with_week(make_state(), days_since_last_run=days)


def test_10_days_not_triggered():
    assert rule_026(_s(10), ComputedVariables(), CFG).triggered is False


def test_14_days_not_triggered_strict():
    # Threshold is strict > 14 days.
    assert rule_026(_s(14), ComputedVariables(), CFG).triggered is False


def test_15_days_triggered():
    out = rule_026(_s(15), ComputedVariables(), CFG)
    assert out.triggered is True
    assert out.plan_hint == "return_from_interruption_progressive"


def test_30_days_triggered_with_plan_hint():
    out = rule_026(_s(30), ComputedVariables(), CFG)
    assert out.triggered is True
    assert out.action == "block_increase"
    assert out.plan_hint == "return_from_interruption_progressive"
