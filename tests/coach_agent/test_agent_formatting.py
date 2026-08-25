from __future__ import annotations

from src.coach_agent.agent import _format_analysis_response
from src.coach_intelligence.domain.schemas.coach_response import CoachResponse
from src.knowledge_engine.domain.schemas.decision import PlanHint


def _response(**overrides) -> CoachResponse:
    defaults = dict(decision_summary="Maintien", main_message="Continue comme ça.")
    defaults.update(overrides)
    return CoachResponse(**defaults)


class _FakeEnvelope:
    def __init__(
        self,
        plan_hints: list[PlanHint],
        target_marathon_pace_min_km: float | None = None,
        target_marathon_pace_source: str = "unavailable",
    ) -> None:
        self.plan_hints = plan_hints
        self.target_marathon_pace_min_km = target_marathon_pace_min_km
        self.target_marathon_pace_source = target_marathon_pace_source


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


def test_analysis_response_includes_pace_line_before_plan_hints():
    envelope = _FakeEnvelope(
        [PlanHint(rule_id="RULE-021", hint="taper_structure", reason="Taper : -50% volume sur 3 sem.")],
        target_marathon_pace_min_km=4.616666,
        target_marathon_pace_source="race_target_time",
    )
    text = _format_analysis_response(_response(), envelope)
    lines = text.splitlines()
    pace_idx = next(i for i, l in enumerate(lines) if "Allure marathon cible" in l)
    taper_idx = next(i for i, l in enumerate(lines) if "Taper :" in l)
    assert pace_idx < taper_idx
