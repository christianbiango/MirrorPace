"""RULE-011 — Feu vert multi-critères (v1.3 C-01 : guard acwr_reliable)."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.progression_rules import rule_011

from tests.knowledge_engine.fixtures.builders import make_state, with_week

CFG = load_default_config()


def _c(acwr=1.0, reliable=True):
    return ComputedVariables(acwr_distance=acwr, acwr_reliable=reliable)


def test_all_green_reliable_triggered():
    state = with_week(make_state(), fatigue_score=2, sleep_quality_score=4, pain_regions=[])
    out = rule_011(state, _c(1.0, True), CFG)
    assert out.triggered is True
    assert out.score_delta == +10


def test_all_green_unreliable_not_triggered():
    """v1.3 C-01 : ACWR non fiable → pas de feu vert malgré tous les autres critères OK."""
    state = with_week(make_state(), fatigue_score=2, sleep_quality_score=4, pain_regions=[])
    out = rule_011(state, _c(1.0, False), CFG)
    assert out.triggered is False


def test_acwr_out_of_sweet_spot_not_triggered():
    state = with_week(make_state(), fatigue_score=2, sleep_quality_score=4)
    assert rule_011(state, _c(1.5, True), CFG).triggered is False


def test_fatigue_too_high_not_triggered():
    state = with_week(make_state(), fatigue_score=3, sleep_quality_score=4)
    assert rule_011(state, _c(1.0, True), CFG).triggered is False


def test_sleep_too_low_not_triggered():
    state = with_week(make_state(), fatigue_score=2, sleep_quality_score=3)
    assert rule_011(state, _c(1.0, True), CFG).triggered is False


def test_acwr_none_not_triggered():
    state = with_week(make_state(), fatigue_score=2, sleep_quality_score=4)
    assert rule_011(state, ComputedVariables(acwr_distance=None, acwr_reliable=True), CFG).triggered is False
