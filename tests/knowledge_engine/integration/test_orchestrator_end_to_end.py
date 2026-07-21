"""End-to-end orchestrator tests — one path per priority tier."""

from src.knowledge_engine import ENGINE_VERSION, SCHEMA_VERSION
from src.knowledge_engine.api import run_engine
from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.runner_state import PainRegion

from tests.knowledge_engine.fixtures.builders import (
    make_state,
    with_context,
    with_profile,
    with_week,
)


CFG = load_default_config()


def test_envelope_shape_defaults():
    """A safe, all-normal week produces a well-formed envelope with the P4 basics."""
    env = run_engine(make_state(), CFG)

    # Meta traceability (GF-05)
    assert env.meta.engine_version == ENGINE_VERSION
    assert env.meta.schema_version == SCHEMA_VERSION
    assert env.meta.config_hash and len(env.meta.config_hash) == 64  # sha256
    assert env.meta.computed_at

    # Decision numeric fields
    assert env.decision.action in {"deload", "decrease", "maintain", "slight_increase", "increase"}
    lo, hi = env.decision.delta_pct_range
    assert lo <= env.decision.delta_pct <= hi
    assert env.decision.absolute_next_week_target_km >= 0

    # Readiness sub-object
    assert 0 <= env.readiness.confidence_score <= 100
    assert set(env.readiness.components.keys()) == {
        "recovery", "load", "progression", "marathon_prep", "p3_adjustments"
    }


def test_p0_pain_critical_short_circuits_to_deload():
    """A single critical pain must deload and post medical_referral."""
    state = make_state()
    state = with_week(
        state,
        pain_regions=[PainRegion(region="knee", intensity=5, days_persistent=3, pain_trend="worsening")],
    )
    env = run_engine(state, CFG)

    assert env.decision.action == "deload"
    assert env.medical_referral is True
    assert env.medical_referral_reason == "pain_critical"
    # All non-P0 triggered rules must be listed in ignored
    triggered_ids = {o.rule_id for o in env.triggered_rules}
    assert "RULE-001" in triggered_ids


def test_p1_taper_forces_decrease():
    """Taper phase (no P0) triggers RULE-007 → force_decrease."""
    state = with_context(make_state(), current_phase="taper", weeks_to_race=2)
    env = run_engine(state, CFG)

    assert env.decision.action == "decrease"
    # Taper delta lives in [-60, -40]
    lo, hi = env.decision.delta_pct_range
    assert lo == -60 and hi == -40
    assert lo <= env.decision.delta_pct <= hi


def test_p2_beginner_caps_slight_increase():
    """Declared beginner : RULE-010 caps the increase to +5%."""
    state = with_profile(
        make_state(),
        experience_level_declared="beginner",
        years_running=0.5,
        recent_race_time_half=None,
    )
    env = run_engine(state, CFG)

    if env.decision.action == "slight_increase":
        assert env.decision.delta_pct <= 5


def test_p3_green_light_bonus_applied():
    """Feu vert multi-critères → +10 pts sur les composantes de readiness."""
    state = make_state()
    # Ensure ACWR is reliable and in sweet spot, all-green metrics
    state = with_week(
        state,
        weekly_distance_history=[40, 40, 40, 40],
        weekly_distance_km=40,
        previous_week_distance_km=40,
        fatigue_score=2,
        sleep_quality_score=4,
        pain_regions=[],
    )
    env = run_engine(state, CFG)
    assert env.readiness.components["p3_adjustments"] == 10


def test_p4_macro_plan_hint_when_far_from_race():
    state = with_context(make_state(), weeks_to_race=20)
    env = run_engine(state, CFG)
    hint_ids = {h.rule_id for h in env.plan_hints}
    assert "RULE-015" in hint_ids
