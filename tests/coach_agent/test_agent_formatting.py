from __future__ import annotations

from src.coach_agent.agent import _format_analysis_response, _format_plan_hints
from src.coach_intelligence.domain.schemas.coach_response import CoachResponse
from src.knowledge_engine.domain.schemas.decision import PlanHint


def _response(**overrides) -> CoachResponse:
    defaults = dict(decision_summary="Maintien", main_message="Continue comme ça.")
    defaults.update(overrides)
    return CoachResponse(**defaults)


class _FakeEnvelope:
    def __init__(self, plan_hints: list[PlanHint]) -> None:
        self.plan_hints = plan_hints


# ── _format_plan_hints ───────────────────────────────────────────────────────

def test_formats_macro_plan_with_phase_breakdown():
    hints = [
        PlanHint(
            rule_id="RULE-015",
            hint="structure_macroplan",
            reason="Macro-plan (18 sem., CV historique 0.10)",
            params={"plan_type": "macro", "suggested_phases": {"general": 7, "specific": 8, "taper": 3}},
        ),
    ]
    lines = _format_plan_hints(hints)
    assert len(lines) == 1
    assert "18 sem." in lines[0]
    assert "7 sem. base" in lines[0]
    assert "8 sem. spécifique" in lines[0]
    assert "3 sem. affûtage" in lines[0]


def test_formats_specific_block_without_general_phase():
    hints = [
        PlanHint(
            rule_id="RULE-027",
            hint="structure_specific_block",
            reason="Fenêtre courte (10 sem.) mais base suffisante",
            params={"plan_type": "specific_block", "suggested_phases": {"specific": 8, "taper": 2}},
        ),
    ]
    lines = _format_plan_hints(hints)
    assert len(lines) == 1
    assert "8 sem. spécifique" in lines[0]
    assert "2 sem. affûtage" in lines[0]
    assert "sem. base" not in lines[0]


def test_formats_other_rules_from_reason_only():
    hints = [
        PlanHint(rule_id="RULE-021", hint="taper_structure", reason="Taper : -50% volume sur 3 sem."),
    ]
    lines = _format_plan_hints(hints)
    assert lines == ["  • Taper : -50% volume sur 3 sem."]


def test_skips_hints_without_reason():
    hints = [PlanHint(rule_id="RULE-022", hint="fill_target_marathon_pace", reason="")]
    assert _format_plan_hints(hints) == []


def test_empty_plan_hints_returns_empty_list():
    assert _format_plan_hints([]) == []


# ── _format_analysis_response ────────────────────────────────────────────────

def test_analysis_response_includes_plan_detail_when_envelope_given():
    envelope = _FakeEnvelope([
        PlanHint(rule_id="RULE-021", hint="taper_structure", reason="Taper : -50% volume sur 3 sem."),
    ])
    text = _format_analysis_response(_response(), envelope)
    assert "Détail du plan (calculé) :" in text
    assert "Taper : -50% volume sur 3 sem." in text


def test_analysis_response_without_envelope_has_no_plan_detail_section():
    text = _format_analysis_response(_response())
    assert "Détail du plan (calculé)" not in text


def test_analysis_response_with_envelope_but_no_triggered_plan_hints():
    envelope = _FakeEnvelope([])
    text = _format_analysis_response(_response(), envelope)
    assert "Détail du plan (calculé)" not in text
