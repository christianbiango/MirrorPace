"""RULE-027 — Structuration spécifique/affûtage en fenêtre courte (v1.3.5 C-19)."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.planning_rules import rule_027

from tests.knowledge_engine.fixtures.builders import make_state, with_context, with_week

CFG = load_default_config()

_READY = ComputedVariables(experience_level="intermediate", chronic_load_distance=40.0)
_REGULAR_HISTORY = [40, 38, 42, 39]


def test_race_none_not_triggered():
    state = with_context(make_state(), weeks_to_race=None)
    assert rule_027(state, _READY, CFG).triggered is False


def test_within_taper_window_not_triggered():
    state = with_context(make_state(), weeks_to_race=2)  # taper_duration_weeks
    assert rule_027(state, _READY, CFG).triggered is False


def test_at_or_above_macro_plan_threshold_not_triggered():
    state = with_context(make_state(), weeks_to_race=16)
    assert rule_027(state, _READY, CFG).triggered is False


def test_history_too_short_not_triggered():
    state = with_context(make_state(), weeks_to_race=10)
    state = with_week(state, weekly_distance_history=[40, 42])
    assert rule_027(state, _READY, CFG).triggered is False


def test_irregular_history_not_triggered():
    state = with_context(make_state(), weeks_to_race=10)
    state = with_week(state, weekly_distance_history=[5, 50, 10, 80])
    assert rule_027(state, _READY, CFG).triggered is False


def test_beginner_below_base_not_triggered():
    """RULE-016's own signal takes priority: not ready for a specific/taper split yet."""
    state = with_context(make_state(), weeks_to_race=10)
    state = with_week(state, weekly_distance_history=_REGULAR_HISTORY)
    computed = ComputedVariables(experience_level="beginner", chronic_load_distance=10.0)
    assert rule_027(state, computed, CFG).triggered is False


def test_triggered_with_ready_athlete_in_short_window():
    state = with_context(make_state(), weeks_to_race=10)
    state = with_week(state, weekly_distance_history=_REGULAR_HISTORY)
    out = rule_027(state, _READY, CFG)

    assert out.triggered is True
    assert out.plan_hint == "structure_specific_block"
    phases = out.extras["suggested_phases"]
    assert phases == {"specific": 8, "taper": 2}
    assert "general" not in phases
