"""RULE-021 — Détail taper (planification)."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.planning_rules import rule_021

from tests.knowledge_engine.fixtures.builders import make_state, with_context

CFG = load_default_config()


def test_non_taper_not_triggered():
    state = with_context(make_state(), current_phase="general")
    assert rule_021(state, ComputedVariables(), CFG).triggered is False


def test_taper_triggered():
    state = with_context(make_state(), current_phase="taper")
    out = rule_021(state, ComputedVariables(), CFG)
    assert out.triggered is True
    assert out.plan_hint == "taper_structure"
    assert out.extras["taper_duration_weeks"] == 3
    assert out.extras["keep_intensity"] is True
    # Midpoint of [-60, -40] → -50 in reduction terms.
    assert out.extras["volume_reduction_pct"] == 50.0
