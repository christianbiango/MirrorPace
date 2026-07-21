"""RULE-002 — Douleur tendon/articulation."""

from src.knowledge_engine.api import PainRegion
from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.safety_rules import rule_002

from tests.knowledge_engine.fixtures.builders import make_state, with_week

CFG = load_default_config()


def _state(pain):
    return with_week(make_state(), pain_regions=pain)


def test_other_region_high_not_triggered():
    pain = [PainRegion(region="other", intensity=5, days_persistent=10)]
    assert rule_002(_state(pain), ComputedVariables(), CFG).triggered is False


def test_knee_exact_threshold_triggered():
    pain = [PainRegion(region="knee", intensity=3, days_persistent=3)]
    out = rule_002(_state(pain), ComputedVariables(), CFG)
    assert out.triggered is True
    assert out.action == "deload"


def test_achilles_below_intensity_not_triggered():
    pain = [PainRegion(region="achilles", intensity=2, days_persistent=5)]
    assert rule_002(_state(pain), ComputedVariables(), CFG).triggered is False
