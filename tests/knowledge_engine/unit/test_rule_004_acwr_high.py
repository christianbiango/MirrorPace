"""RULE-004 — ACWR élevé."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.progression_rules import rule_004

from tests.knowledge_engine.fixtures.builders import make_state

CFG = load_default_config()
STATE = make_state()


def test_acwr_1_4_not_triggered():
    assert rule_004(STATE, ComputedVariables(acwr_distance=1.4, acwr_reliable=True), CFG).triggered is False


def test_acwr_1_5_exact_not_triggered_strict():
    assert rule_004(STATE, ComputedVariables(acwr_distance=1.5, acwr_reliable=True), CFG).triggered is False


def test_acwr_1_6_triggered():
    out = rule_004(STATE, ComputedVariables(acwr_distance=1.6, acwr_reliable=True), CFG)
    assert out.triggered is True and out.action == "block_increase"


def test_acwr_2_0_not_triggered_here():
    # RULE-003 handles ≥ 2.0
    assert rule_004(STATE, ComputedVariables(acwr_distance=2.0, acwr_reliable=True), CFG).triggered is False
