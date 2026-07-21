"""P-17 — Pathologie connue mais aucune douleur cette semaine.

Attendu : le medical_referral doit être posé (motif "known_pathology")
sans qu'aucune règle de douleur (RULE-001/RULE-002) ne déclenche.
"""

from src.knowledge_engine.api import run_engine
from src.knowledge_engine.config.loader import load_default_config

from tests.knowledge_engine.fixtures.builders import make_state, with_profile, with_week


CFG = load_default_config()


def test_known_pathology_without_active_pain_flags_referral_only():
    state = make_state()
    state = with_profile(state, pathologies_connues=["achilles_tendinopathy_chronic"])
    state = with_week(state, pain_regions=[])

    env = run_engine(state, CFG)

    # Referral is posted
    assert env.medical_referral is True
    assert env.medical_referral_reason == "known_pathology"

    # Neither RULE-001 nor RULE-002 fired (no pain in the week)
    triggered_ids = {o.rule_id for o in env.triggered_rules if o.triggered}
    assert "RULE-001" not in triggered_ids
    assert "RULE-002" not in triggered_ids
