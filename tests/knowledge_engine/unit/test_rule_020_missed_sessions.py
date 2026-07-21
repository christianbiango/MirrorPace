"""RULE-020 — Séances manquées (v1.3 C-07 : exclude fatigue_trend=unknown)."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.planning_rules import rule_020

from tests.knowledge_engine.fixtures.builders import make_state

CFG = load_default_config()
STATE = make_state()


def _c(delta, trend):
    return ComputedVariables(delta_volume_pct=delta, fatigue_trend=trend)


def test_delta_none_not_triggered():
    assert rule_020(STATE, _c(None, "improving"), CFG).triggered is False


def test_delta_positive_not_triggered():
    assert rule_020(STATE, _c(+5.0, "improving"), CFG).triggered is False


def test_delta_negative_moderate_not_triggered():
    # -10% not below -20% threshold.
    assert rule_020(STATE, _c(-10.0, "improving"), CFG).triggered is False


def test_delta_severe_and_improving_triggered():
    out = rule_020(STATE, _c(-25.0, "improving"), CFG)
    assert out.triggered is True
    assert out.plan_hint == "adjust_next_week_no_catchup"


def test_delta_severe_and_stable_triggered():
    assert rule_020(STATE, _c(-25.0, "stable"), CFG).triggered is True


def test_delta_severe_and_worsening_not_triggered():
    assert rule_020(STATE, _c(-25.0, "worsening"), CFG).triggered is False


def test_delta_severe_and_unknown_not_triggered():
    """v1.3 C-07 : fatigue_trend='unknown' must NOT trigger this rule."""
    assert rule_020(STATE, _c(-25.0, "unknown"), CFG).triggered is False
