"""RULE-008 — Blessure récente."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.progression_rules import rule_008

from tests.knowledge_engine.fixtures.builders import make_state, with_context

CFG = load_default_config()


def _s(weeks):
    return with_context(make_state(), weeks_since_last_injury=weeks)


def test_null_injury_not_triggered():
    assert rule_008(_s(None), ComputedVariables(), CFG).triggered is False


def test_2_weeks_triggered():
    out = rule_008(_s(2), ComputedVariables(), CFG)
    assert out.triggered is True and out.cap_pct == 5


def test_4_weeks_not_triggered_strict():
    assert rule_008(_s(4), ComputedVariables(), CFG).triggered is False


def test_6_weeks_not_triggered():
    assert rule_008(_s(6), ComputedVariables(), CFG).triggered is False
