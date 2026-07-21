"""KB v1.3.1 C-15 — property tests for GF-06 / GF-07 / P0 interaction.

C-15a : if P0 fires, GF-06 must NOT downgrade "deload" (it's the highest severity anyway,
         but the contract requires the guard to be explicit).
C-15b : GF-07 (taper → decrease) must be respected UNLESS P0 fires (in which case P0 wins → deload).
"""

from dataclasses import replace

from src.knowledge_engine.api import run_engine
from src.knowledge_engine.config.loader import load_default_config

from tests.knowledge_engine.fixtures.builders import (
    make_state,
    with_context,
    with_profile,
    with_week,
)
from src.knowledge_engine.domain.schemas.runner_state import PainRegion


CFG = load_default_config()


# --------------------------------------------------------------------------- #
# C-15a — P0 + low-confidence : action must remain "deload"
# --------------------------------------------------------------------------- #

def _low_confidence_state():
    """A state whose readiness_confidence_score is far below the high threshold."""
    state = make_state()
    state = with_profile(
        state,
        VMA_kmh=None,
        recent_race_time_10k=None,
        recent_race_time_half=None,
        race_target_time=None,
        experience_level_declared="beginner",
    )
    state = with_week(
        state,
        weekly_distance_history=[],  # no ACWR history
        avg_weekly_RPE=None,
        long_run_km_last_week=0,
        long_run_km_previous_week=None,
        days_since_last_run=20,  # long interruption
    )
    return state


def test_p0_pain_critical_low_confidence_still_deloads():
    state = _low_confidence_state()
    state = with_week(
        state,
        pain_regions=[PainRegion(region="knee", intensity=5, days_persistent=3, pain_trend="worsening")],
    )
    env = run_engine(state, CFG)
    assert env.decision.action == "deload"


def test_p0_pain_tendon_low_confidence_still_deloads():
    state = _low_confidence_state()
    state = with_week(
        state,
        pain_regions=[PainRegion(region="achilles", intensity=3, days_persistent=5, pain_trend="worsening")],
    )
    env = run_engine(state, CFG)
    assert env.decision.action == "deload"


def test_p0_acwr_danger_low_confidence_still_deloads():
    # ACWR ≥ 2.0 requires reliable ACWR. Give a stable 4-week history at 20 km,
    # then jump to 45 km (ratio = 2.25).
    state = _low_confidence_state()
    state = with_week(
        state,
        weekly_distance_history=[20, 20, 20, 20],
        weekly_distance_km=45,
        previous_week_distance_km=20,
    )
    env = run_engine(state, CFG)
    assert env.decision.action == "deload"


# --------------------------------------------------------------------------- #
# C-15b — Taper + P0 → deload; Taper without P0 → decrease
# --------------------------------------------------------------------------- #

def _taper_state():
    """Taper phase, all-safe."""
    state = make_state()
    state = with_context(state, current_phase="taper", weeks_to_race=2)
    return state


def test_taper_no_p0_decreases():
    env = run_engine(_taper_state(), CFG)
    assert env.decision.action == "decrease"


def test_taper_plus_p0_pain_critical_deloads():
    state = _taper_state()
    state = with_week(
        state,
        pain_regions=[PainRegion(region="knee", intensity=5, days_persistent=3, pain_trend="worsening")],
    )
    env = run_engine(state, CFG)
    assert env.decision.action == "deload"


def test_taper_plus_p0_pain_tendon_deloads():
    state = _taper_state()
    state = with_week(
        state,
        pain_regions=[PainRegion(region="achilles", intensity=3, days_persistent=5, pain_trend="worsening")],
    )
    env = run_engine(state, CFG)
    assert env.decision.action == "deload"
