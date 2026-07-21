"""RULE-010 — Beginner cap."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.progression_rules import rule_010

from tests.knowledge_engine.fixtures.builders import make_state

CFG = load_default_config()
STATE = make_state()


def _c(level):
    return ComputedVariables(experience_level=level)


def test_beginner_triggered():
    out = rule_010(STATE, _c("beginner"), CFG)
    assert out.triggered is True and out.cap_pct == 5


def test_intermediate_not_triggered():
    assert rule_010(STATE, _c("intermediate"), CFG).triggered is False


def test_advanced_not_triggered():
    assert rule_010(STATE, _c("advanced"), CFG).triggered is False
