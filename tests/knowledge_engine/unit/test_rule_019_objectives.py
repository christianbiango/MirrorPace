"""RULE-019 — Objectifs incohérents (Riegel vs target)."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.planning_rules import rule_019

from tests.knowledge_engine.fixtures.builders import make_state, with_profile

CFG = load_default_config()


def test_no_half_not_triggered():
    state = with_profile(make_state(), recent_race_time_half=None, race_target_time=3 * 3600)
    assert rule_019(state, ComputedVariables(), CFG).triggered is False


def test_no_target_not_triggered():
    state = with_profile(make_state(), recent_race_time_half=5700, race_target_time=None)
    assert rule_019(state, ComputedVariables(), CFG).triggered is False


def test_realistic_target_not_triggered():
    # Half 1h35 (5700s) → Riegel marathon ≈ 5700*2^1.06 ≈ 11 900 s (~3h18).
    # Target 3h20 (12000s) → gap ~1% ≤ 15% → not triggered.
    state = with_profile(make_state(), recent_race_time_half=5700, race_target_time=12000)
    assert rule_019(state, ComputedVariables(), CFG).triggered is False


def test_overly_ambitious_target_triggered():
    # Half 1h35 → predicted ~3h18. Target 2h30 (9000s) → gap ~32% > 15% → triggered.
    state = with_profile(make_state(), recent_race_time_half=5700, race_target_time=9000)
    out = rule_019(state, ComputedVariables(), CFG)
    assert out.triggered is True
    assert out.plan_hint == "revise_objectives"
