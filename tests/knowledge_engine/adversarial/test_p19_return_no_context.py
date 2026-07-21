"""P-19 — Retour d'interruption sans blessure connue.

Attendu : jours_since_last_run > 14 déclenche RULE-026 même sans
weeks_since_last_injury renseigné (RULE-008 reste inactive), et un
plan_hint "return_from_interruption_progressive" est exposé.
"""

from src.knowledge_engine.api import run_engine
from src.knowledge_engine.config.loader import load_default_config

from tests.knowledge_engine.fixtures.builders import make_state, with_context, with_week


CFG = load_default_config()


def test_interruption_without_injury_context():
    state = make_state()
    state = with_context(state, weeks_since_last_injury=None)
    state = with_week(state, days_since_last_run=21)

    env = run_engine(state, CFG)

    triggered_ids = {o.rule_id for o in env.triggered_rules if o.triggered}
    assert "RULE-026" in triggered_ids
    assert "RULE-008" not in triggered_ids

    hints = {h.hint for h in env.plan_hints}
    assert "return_from_interruption_progressive" in hints

    # Interruption → block_increase → maintain (unless overridden by higher priority)
    assert env.decision.action in {"maintain", "decrease", "deload"}
