"""RULE-025 — Nutrition course : protocole CHO."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.race_day_rules import rule_025

from tests.knowledge_engine.fixtures.builders import make_state

CFG = load_default_config()
STATE = make_state()


def test_pace_none_not_triggered():
    assert rule_025(STATE, ComputedVariables(target_marathon_pace_min_km=None), CFG).triggered is False


def test_fast_runner_under_90min_not_triggered():
    # Elite pace 2 min/km * 42.195 ≈ 84 min ≤ 90 min → not triggered.
    assert rule_025(STATE, ComputedVariables(target_marathon_pace_min_km=2.0), CFG).triggered is False


def test_regular_runner_over_90min_triggered():
    # 5 min/km * 42.195 ≈ 211 min > 90 min → triggered.
    out = rule_025(STATE, ComputedVariables(target_marathon_pace_min_km=5.0), CFG)
    assert out.triggered is True
    assert out.plan_hint == "cho_protocol_60_90g_per_hour"
    assert out.extras["cho_min_g_per_hour"] == 60
    assert out.extras["cho_max_g_per_hour"] == 90
