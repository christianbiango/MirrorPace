"""RULE-022 — Calcul allure marathon cible : signale l'absence d'allure calculée."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.planning_rules import rule_022

from tests.knowledge_engine.fixtures.builders import make_state, with_profile

CFG = load_default_config()


def test_pace_already_computed_not_triggered():
    state = make_state()
    computed = ComputedVariables(target_marathon_pace_min_km=5.0)
    assert rule_022(state, computed, CFG).triggered is False


def test_no_pace_no_sources_not_triggered():
    state = with_profile(
        make_state(),
        recent_race_time_half=None,
        recent_race_time_10k=None,
        VMA_kmh=None,
        race_target_time=None,
    )
    computed = ComputedVariables(target_marathon_pace_min_km=None)
    assert rule_022(state, computed, CFG).triggered is False


def test_no_pace_with_sources_triggered():
    # Default builder has recent_race_time_half=5700 + VMA_kmh=16.0.
    state = make_state()
    computed = ComputedVariables(target_marathon_pace_min_km=None)
    out = rule_022(state, computed, CFG)
    assert out.triggered is True
    assert out.plan_hint == "fill_target_marathon_pace"
