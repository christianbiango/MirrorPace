"""RULE-001 — Douleur critique (KB v1.2 §3 tests_expected)."""

from src.knowledge_engine.api import PainRegion
from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.computed import ComputedVariables
from src.knowledge_engine.rules.safety_rules import rule_001

from tests.knowledge_engine.fixtures.builders import make_state, with_week


CFG = load_default_config()


def _state(pain: list[PainRegion]):
    return with_week(make_state(), pain_regions=pain)


def test_no_pain_not_triggered():
    out = rule_001(_state([]), ComputedVariables(), CFG)
    assert out.triggered is False


def test_below_intensity_not_triggered():
    pain = [PainRegion(region="calf", intensity=3, days_persistent=5)]
    out = rule_001(_state(pain), ComputedVariables(), CFG)
    assert out.triggered is False


def test_below_days_not_triggered():
    pain = [PainRegion(region="calf", intensity=4, days_persistent=1)]
    out = rule_001(_state(pain), ComputedVariables(), CFG)
    assert out.triggered is False


def test_exact_threshold_triggered():
    pain = [PainRegion(region="calf", intensity=4, days_persistent=2)]
    out = rule_001(_state(pain), ComputedVariables(), CFG)
    assert out.triggered is True
    assert out.action == "deload"
    assert out.medical_referral is True
    assert out.short_circuit is True


def test_extreme_short_not_triggered():
    pain = [PainRegion(region="calf", intensity=5, days_persistent=1)]
    out = rule_001(_state(pain), ComputedVariables(), CFG)
    assert out.triggered is False


def test_multiple_regions_one_meets():
    pain = [
        PainRegion(region="calf", intensity=2, days_persistent=10),
        PainRegion(region="knee", intensity=5, days_persistent=3),
    ]
    out = rule_001(_state(pain), ComputedVariables(), CFG)
    assert out.triggered is True
    assert "knee" in out.reason


def test_zero_intensity_entry_not_triggered():
    pain = [PainRegion(region="calf", intensity=0, days_persistent=10)]
    out = rule_001(_state(pain), ComputedVariables(), CFG)
    assert out.triggered is False
