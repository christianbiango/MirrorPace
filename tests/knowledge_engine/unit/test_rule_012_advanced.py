"""RULE-012 — Tolérance avancée."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.progression_rules import rule_012

from tests.knowledge_engine.fixtures.builders import make_state

CFG = load_default_config()
STATE = make_state()


def _c(level, acwr=1.0):
    return ComputedVariables(experience_level=level, acwr_distance=acwr)


def test_advanced_sweet_spot_triggered():
    out = rule_012(STATE, _c("advanced", 1.0), CFG)
    assert out.triggered is True
    assert out.score_delta == +5


def test_intermediate_not_triggered():
    assert rule_012(STATE, _c("intermediate", 1.0), CFG).triggered is False


def test_advanced_out_of_sweet_spot_not_triggered():
    assert rule_012(STATE, _c("advanced", 1.5), CFG).triggered is False


def test_advanced_acwr_none_not_triggered():
    assert rule_012(STATE, _c("advanced", None), CFG).triggered is False
