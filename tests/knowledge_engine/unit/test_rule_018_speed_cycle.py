"""RULE-018 — Cycle vitesse/seuil pré-marathon."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.planning_rules import rule_018

from tests.knowledge_engine.fixtures.builders import make_state, with_context, with_profile

CFG = load_default_config()


def _c(pace):
    return ComputedVariables(target_marathon_pace_min_km=pace)


def test_too_close_to_race_not_triggered():
    state = with_context(make_state(), weeks_to_race=6)
    assert rule_018(state, _c(5.0), CFG).triggered is False


def test_weeks_to_race_none_not_triggered():
    state = with_context(make_state(), weeks_to_race=None)
    assert rule_018(state, _c(5.0), CFG).triggered is False


def test_missing_10k_not_triggered():
    state = with_context(make_state(), weeks_to_race=16)
    state = with_profile(state, recent_race_time_10k=None)
    assert rule_018(state, _c(5.0), CFG).triggered is False


def test_10k_below_potential_triggered():
    # Target marathon pace 5.0 min/km → t_marathon ≈ 210 min → predicted 10k ≈ 44.4 min.
    # Runner runs 10k in 55 min (> +5% tolerance) → 10k below potential → triggered.
    state = with_context(make_state(), weeks_to_race=16)
    state = with_profile(state, recent_race_time_10k=55 * 60)
    out = rule_018(state, _c(5.0), CFG)
    assert out.triggered is True
    assert out.plan_hint == "speed_threshold_cycle_recommended"


def test_10k_matches_potential_not_triggered():
    state = with_context(make_state(), weeks_to_race=16)
    state = with_profile(state, recent_race_time_10k=45 * 60)
    assert rule_018(state, _c(5.0), CFG).triggered is False
