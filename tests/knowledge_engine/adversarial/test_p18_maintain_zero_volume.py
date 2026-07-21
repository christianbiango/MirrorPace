"""P-18 — Semaine à volume nul avec maintien.

Attendu : quand l'action agrégée est "maintain" et la semaine est à zéro km,
le plancher `min_absolute_weekly_km_on_maintain` (v1.3 C-09) empêche
un objectif absolu à 0 km.
"""

from src.knowledge_engine.api import run_engine
from src.knowledge_engine.config.loader import load_default_config

from tests.knowledge_engine.fixtures.builders import make_state, with_week


CFG = load_default_config()


def test_zero_volume_maintain_falls_back_to_floor():
    # A missed week with high fatigue triggers RULE-006 (P1 block_increase → maintain).
    state = make_state()
    state = with_week(
        state,
        weekly_distance_km=0,
        previous_week_distance_km=40,
        long_run_km_last_week=0,
        fatigue_score=5,
        sleep_quality_score=1,
    )
    env = run_engine(state, CFG)

    # Sanity : action is maintain
    assert env.decision.action == "maintain"
    # v1.3 C-09 floor kicks in : ≥ min_absolute_weekly_km_on_maintain (5 km)
    assert env.decision.absolute_next_week_target_km >= 5.0
