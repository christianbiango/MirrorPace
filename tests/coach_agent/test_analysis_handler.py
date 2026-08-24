from __future__ import annotations

from datetime import date

import pytest

from src.coach_agent.handlers.analysis_handler import (
    build_plan_context,
    derive_current_phase,
    weeks_to_race,
)
from src.knowledge_engine.config.loader import load_default_config
from src.knowledge_engine.domain.schemas.runner_state import RunnerProfile

CFG = load_default_config()


def _profile(**overrides) -> RunnerProfile:
    defaults = dict(
        age=30,
        experience_level_declared="intermediate",
        sessions_per_week_available=4,
    )
    defaults.update(overrides)
    return RunnerProfile(**defaults)


# ── weeks_to_race ────────────────────────────────────────────────────────────

def test_weeks_to_race_none_when_no_target_date():
    assert weeks_to_race(_profile(), date(2026, 1, 1)) is None


def test_weeks_to_race_none_when_race_already_passed():
    profile = _profile(race_target_date="2025-12-01")
    assert weeks_to_race(profile, date(2026, 1, 1)) is None


def test_weeks_to_race_computes_whole_weeks():
    profile = _profile(race_target_date="2026-05-01")  # 16 weeks after 2026-01-10
    assert weeks_to_race(profile, date(2026, 1, 10)) == 15


def test_weeks_to_race_zero_on_race_day():
    profile = _profile(race_target_date="2026-01-10")
    assert weeks_to_race(profile, date(2026, 1, 10)) == 0


# ── derive_current_phase ─────────────────────────────────────────────────────

def test_phase_general_when_no_race_set():
    assert derive_current_phase(None, CFG) == "general"


def test_phase_taper_within_taper_duration():
    taper_weeks = CFG.get("taper_duration_weeks")
    assert derive_current_phase(taper_weeks, CFG) == "taper"
    assert derive_current_phase(0, CFG) == "taper"


def test_phase_specific_marathon_mid_range():
    assert derive_current_phase(8, CFG) == "specific_marathon"


def test_phase_general_when_far_from_race():
    assert derive_current_phase(20, CFG) == "general"


# ── build_plan_context ───────────────────────────────────────────────────────

def test_build_plan_context_wires_weeks_and_phase():
    profile = _profile(race_target_date="2026-02-01")  # 3 weeks after 2026-01-10
    ctx = build_plan_context(profile, CFG, date(2026, 1, 10))
    assert ctx.weeks_to_race == 3
    assert ctx.current_phase == "taper"


def test_build_plan_context_defaults_when_no_race():
    ctx = build_plan_context(_profile(), CFG, date(2026, 1, 10))
    assert ctx.weeks_to_race is None
    assert ctx.current_phase == "general"
