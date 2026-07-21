"""KB v1.3.1 C-14 — normative tests for `resolve_medical_referral`."""

from dataclasses import dataclass

from src.knowledge_engine.engine.envelope_builder import resolve_medical_referral


@dataclass
class _RO:
    rule_id: str
    triggered: bool


def test_case_1_all_three_pain_critical_wins():
    ref, reason = resolve_medical_referral(
        [_RO("RULE-001", True), _RO("RULE-002", True)],
        ["arythmie"],
    )
    assert ref is True and reason == "pain_critical"


def test_case_2_pain_critical_and_pathology():
    ref, reason = resolve_medical_referral(
        [_RO("RULE-001", True), _RO("RULE-002", False)],
        ["arythmie"],
    )
    assert ref is True and reason == "pain_critical"


def test_case_3_pain_tendon_and_pathology():
    ref, reason = resolve_medical_referral(
        [_RO("RULE-001", False), _RO("RULE-002", True)],
        ["arythmie"],
    )
    assert ref is True and reason == "pain_tendon"


def test_case_4_pathology_alone():
    ref, reason = resolve_medical_referral(
        [_RO("RULE-001", False), _RO("RULE-002", False)],
        ["arythmie"],
    )
    assert ref is True and reason == "known_pathology"


def test_case_5_nothing():
    ref, reason = resolve_medical_referral(
        [_RO("RULE-001", False)],
        [],
    )
    assert ref is False and reason is None


def test_case_6_pain_critical_only():
    ref, reason = resolve_medical_referral(
        [_RO("RULE-001", True)],
        [],
    )
    assert ref is True and reason == "pain_critical"


def test_case_7_pain_tendon_only():
    ref, reason = resolve_medical_referral(
        [_RO("RULE-001", False), _RO("RULE-002", True)],
        [],
    )
    assert ref is True and reason == "pain_tendon"


def test_invariant_medical_ref_false_implies_reason_none():
    ref, reason = resolve_medical_referral([], [])
    assert (ref is False) and (reason is None)
