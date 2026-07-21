"""RULE-005 — Progression volume > 10%."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.progression_rules import rule_005

from tests.knowledge_engine.fixtures.builders import make_state

CFG = load_default_config()
STATE = make_state()


def test_small_prev_week_guard_not_triggered():
    # delta_volume_reliable=False → guard
    assert rule_005(STATE, ComputedVariables(delta_volume_pct=50.0, delta_volume_reliable=False), CFG).triggered is False


def test_big_prev_delta_9_not_triggered():
    assert rule_005(STATE, ComputedVariables(delta_volume_pct=9.0, delta_volume_reliable=True), CFG).triggered is False


def test_big_prev_delta_11_triggered():
    out = rule_005(STATE, ComputedVariables(delta_volume_pct=11.0, delta_volume_reliable=True), CFG)
    assert out.triggered is True and out.action == "block_increase"


def test_negative_delta_not_triggered():
    assert rule_005(STATE, ComputedVariables(delta_volume_pct=-15.0, delta_volume_reliable=True), CFG).triggered is False
