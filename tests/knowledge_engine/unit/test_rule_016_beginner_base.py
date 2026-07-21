"""RULE-016 — Beginner : cycle préparatoire d'abord."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.planning_rules import rule_016

from tests.knowledge_engine.fixtures.builders import make_state

CFG = load_default_config()
STATE = make_state()


def _c(level, chronic_load):
    return ComputedVariables(experience_level=level, chronic_load_distance=chronic_load)


def test_beginner_low_base_triggered():
    out = rule_016(STATE, _c("beginner", 15), CFG)
    assert out.triggered is True
    assert out.plan_hint == "preparatory_cycle_before_marathon_specific"


def test_beginner_high_base_not_triggered():
    assert rule_016(STATE, _c("beginner", 30), CFG).triggered is False


def test_intermediate_low_base_not_triggered():
    assert rule_016(STATE, _c("intermediate", 15), CFG).triggered is False
