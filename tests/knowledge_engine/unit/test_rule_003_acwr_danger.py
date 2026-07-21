"""RULE-003 — ACWR danger."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.safety_rules import rule_003

from tests.knowledge_engine.fixtures.builders import make_state

CFG = load_default_config()
STATE = make_state()


def test_acwr_unreliable_high_ratio_not_triggered():
    c = ComputedVariables(acwr_distance=2.5, acwr_reliable=False)
    assert rule_003(STATE, c, CFG).triggered is False


def test_acwr_reliable_below_not_triggered():
    c = ComputedVariables(acwr_distance=1.9, acwr_reliable=True)
    assert rule_003(STATE, c, CFG).triggered is False


def test_acwr_reliable_exact_triggered():
    c = ComputedVariables(acwr_distance=2.0, acwr_reliable=True)
    out = rule_003(STATE, c, CFG)
    assert out.triggered is True and out.action == "deload"


def test_acwr_null_not_triggered():
    c = ComputedVariables(acwr_distance=None, acwr_reliable=False)
    assert rule_003(STATE, c, CFG).triggered is False
