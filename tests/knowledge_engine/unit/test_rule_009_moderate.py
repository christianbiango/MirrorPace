"""RULE-009 — Fatigue/sommeil modéré."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.progression_rules import rule_009

from tests.knowledge_engine.fixtures.builders import make_state, with_week

CFG = load_default_config()


def _s(fat, sleep):
    return with_week(make_state(), fatigue_score=fat, sleep_quality_score=sleep)


def test_fatigue_3_sleep_5_triggered():
    assert rule_009(_s(3, 5), ComputedVariables(), CFG).triggered is True


def test_fatigue_5_sleep_3_triggered():
    # In orchestration, RULE-006 P1 would win — but this unit test verifies the rule itself.
    assert rule_009(_s(5, 3), ComputedVariables(), CFG).triggered is True


def test_fatigue_2_sleep_2_not_triggered():
    assert rule_009(_s(2, 2), ComputedVariables(), CFG).triggered is False
