from __future__ import annotations

from src.coach_agent.formatting import (
    format_pace_min_per_km,
    format_plan_hints,
    format_target_pace,
)
from src.knowledge_engine.domain.schemas.decision import PlanHint


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


# ── format_plan_hints ────────────────────────────────────────────────────────

def test_formats_macro_plan_with_phase_breakdown():
    hints = [
        PlanHint(
            rule_id="RULE-015",
            hint="structure_macroplan",
            reason="Macro-plan (18 sem., CV historique 0.10)",
            params={"plan_type": "macro", "suggested_phases": {"general": 7, "specific": 8, "taper": 3}},
        ),
    ]
    lines = format_plan_hints(hints)
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
    lines = format_plan_hints(hints)
    assert len(lines) == 1
    assert "8 sem. spécifique" in lines[0]
    assert "2 sem. affûtage" in lines[0]
    assert "sem. base" not in lines[0]


def test_formats_other_rules_from_reason_only():
    hints = [
        PlanHint(rule_id="RULE-021", hint="taper_structure", reason="Taper : -50% volume sur 3 sem."),
    ]
    assert format_plan_hints(hints) == ["Taper : -50% volume sur 3 sem."]


def test_skips_hints_without_reason():
    hints = [PlanHint(rule_id="RULE-022", hint="fill_target_marathon_pace", reason="")]
    assert format_plan_hints(hints) == []


def test_empty_plan_hints_returns_empty_list():
    assert format_plan_hints([]) == []


# ── format_pace_min_per_km / format_target_pace ─────────────────────────────

def test_formats_pace_rounding_down():
    assert format_pace_min_per_km(4.616666) == "4:37"


def test_formats_pace_rounds_seconds_up_to_next_minute():
    assert format_pace_min_per_km(4.999) == "5:00"


def test_target_pace_none_when_unavailable():
    envelope = _FakeEnvelope([], target_marathon_pace_min_km=None)
    assert format_target_pace(envelope) is None


def test_target_pace_line_includes_source_label():
    envelope = _FakeEnvelope(
        [], target_marathon_pace_min_km=4.616666, target_marathon_pace_source="race_target_time"
    )
    line = format_target_pace(envelope)
    assert "4:37/km" in line
    assert "objectif déclaré" in line
