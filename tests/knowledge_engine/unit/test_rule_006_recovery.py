"""RULE-006 — Récupération insuffisante."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.progression_rules import rule_006

from tests.knowledge_engine.fixtures.builders import make_state, with_week

CFG = load_default_config()


def _s(fat, sleep):
    return with_week(make_state(), fatigue_score=fat, sleep_quality_score=sleep)


def test_fatigue_5_sleep_5_triggered_via_extreme():
    assert rule_006(_s(5, 5), ComputedVariables(), CFG).triggered is True


def test_fatigue_4_sleep_5_not_triggered():
    assert rule_006(_s(4, 5), ComputedVariables(), CFG).triggered is False


def test_fatigue_4_sleep_2_triggered_combo():
    out = rule_006(_s(4, 2), ComputedVariables(), CFG)
    assert out.triggered is True and out.action == "block_increase"


def test_fatigue_3_sleep_1_not_triggered_here():
    # RULE-009 (P2) handles moderate
    assert rule_006(_s(3, 1), ComputedVariables(), CFG).triggered is False


def test_fatigue_5_sleep_1_triggered():
    assert rule_006(_s(5, 1), ComputedVariables(), CFG).triggered is True
