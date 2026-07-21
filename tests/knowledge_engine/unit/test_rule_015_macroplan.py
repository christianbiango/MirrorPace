"""RULE-015 — Macro-plan structure."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.planning_rules import rule_015

from tests.knowledge_engine.fixtures.builders import make_state, with_context, with_week

CFG = load_default_config()


def test_race_too_close_not_triggered():
    state = with_context(make_state(), weeks_to_race=10)
    assert rule_015(state, ComputedVariables(), CFG).triggered is False


def test_race_none_not_triggered():
    state = with_context(make_state(), weeks_to_race=None)
    assert rule_015(state, ComputedVariables(), CFG).triggered is False


def test_history_too_short_not_triggered():
    state = with_context(make_state(), weeks_to_race=20)
    state = with_week(state, weekly_distance_history=[40, 42])
    assert rule_015(state, ComputedVariables(), CFG).triggered is False


def test_irregular_history_not_triggered():
    state = with_context(make_state(), weeks_to_race=20)
    state = with_week(state, weekly_distance_history=[5, 50, 10, 80])
    assert rule_015(state, ComputedVariables(), CFG).triggered is False


def test_regular_history_triggered():
    state = with_context(make_state(), weeks_to_race=20)
    state = with_week(state, weekly_distance_history=[42, 40, 38, 36])
    out = rule_015(state, ComputedVariables(), CFG)
    assert out.triggered is True
    assert out.plan_hint == "structure_macroplan"
    assert "suggested_phases" in out.extras
    phases = out.extras["suggested_phases"]
    assert set(phases.keys()) == {"general", "specific", "taper"}
    assert phases["taper"] == 3
