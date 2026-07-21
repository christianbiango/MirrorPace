"""P-16 — Faux feu vert : ACWR "vert" mais historique insuffisant → RULE-011 doit NE PAS déclencher.

v1.3 C-01 : the acwr_reliable guard added to RULE-011 covers this case.
"""

from src.knowledge_engine.api import run_engine
from src.knowledge_engine.config.loader import load_default_config

from tests.knowledge_engine.fixtures.builders import make_state, with_week


CFG = load_default_config()


def test_short_history_does_not_trigger_green_light():
    # Only 2 weeks of history — ACWR is not reliable → RULE-011 must stay OFF.
    state = make_state()
    state = with_week(
        state,
        weekly_distance_history=[40, 42],  # < acwr_min_history_weeks = 4
        weekly_distance_km=42,
        previous_week_distance_km=40,
        fatigue_score=2,
        sleep_quality_score=4,
        pain_regions=[],
    )
    env = run_engine(state, CFG)

    # The green-light bonus (+10) must NOT be applied.
    assert env.readiness.components["p3_adjustments"] == 0
    # Overall action is safe default → the runner is not falsely encouraged.
    assert env.decision.action in {"increase", "slight_increase", "maintain"}
