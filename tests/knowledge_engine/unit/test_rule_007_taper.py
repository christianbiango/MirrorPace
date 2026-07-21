"""RULE-007 — Phase taper : force_decrease."""

from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.progression_rules import rule_007

from tests.knowledge_engine.fixtures.builders import make_state, with_context

CFG = load_default_config()


def test_phase_general_not_triggered():
    assert rule_007(with_context(make_state(), current_phase="general"), ComputedVariables(), CFG).triggered is False


def test_phase_specific_not_triggered():
    assert rule_007(with_context(make_state(), current_phase="specific_marathon"), ComputedVariables(), CFG).triggered is False


def test_phase_taper_triggered_with_range():
    out = rule_007(with_context(make_state(), current_phase="taper"), ComputedVariables(), CFG)
    assert out.triggered is True
    assert out.action == "force_decrease"
    lo, hi = out.extras["target_delta_range"]
    assert out.target_delta_pct is not None
    assert lo <= out.target_delta_pct <= hi
    assert lo == -60 and hi == -40
