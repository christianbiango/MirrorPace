from __future__ import annotations

from datetime import date

import pytest

from src.coach_intelligence.personalizer.runner_personalizer import RunnerPersonalizer
from src.knowledge_engine.api import PlanContext, RunnerProfile
from tests.coach_intelligence.conftest import make_snapshot


@pytest.fixture
def personalizer() -> RunnerPersonalizer:
    return RunnerPersonalizer()


def _default_context(weeks_to_race: int | None = None) -> PlanContext:
    return PlanContext(weeks_to_race=weeks_to_race)


def _profile(
    experience: str = "intermediate",
    years: float | None = None,
    race_target: int | None = None,
) -> RunnerProfile:
    return RunnerProfile(
        age=30,
        experience_level_declared=experience,
        sessions_per_week_available=4,
        years_running=years,
        race_target_time=race_target,
    )


def test_advanced_declared_gets_technical(personalizer):
    snap = make_snapshot(total_activities=10)
    result = personalizer.personalize(snap, _profile(experience="advanced"), _default_context())
    assert result.communication_style == "technical"


def test_years_running_3_gets_technical(personalizer):
    snap = make_snapshot(total_activities=10)
    result = personalizer.personalize(snap, _profile(experience="beginner", years=3.0), _default_context())
    assert result.communication_style == "technical"


def test_100_activities_gets_technical(personalizer):
    snap = make_snapshot(total_activities=100)
    result = personalizer.personalize(snap, _profile(experience="beginner"), _default_context())
    assert result.communication_style == "technical"


def test_beginner_gets_simple(personalizer):
    snap = make_snapshot(total_activities=10)
    result = personalizer.personalize(snap, _profile(experience="beginner", years=0.5), _default_context())
    assert result.communication_style == "simple"


def test_career_context_with_active_since(personalizer):
    snap = make_snapshot(active_since=date(2022, 1, 1))
    result = personalizer.personalize(snap, _profile(), _default_context())
    assert "ans" in result.career_context
    assert "km" in result.career_context
    assert "activités" in result.career_context


def test_career_context_without_active_since(personalizer):
    snap = make_snapshot()
    snap.active_since = None
    result = personalizer.personalize(snap, _profile(), _default_context())
    assert "ans" not in result.career_context
    assert "km" in result.career_context
    assert "activités" in result.career_context


def test_fitness_note_improving(personalizer):
    snap = make_snapshot(fitness_trend="improving")
    result = personalizer.personalize(snap, _profile(), _default_context())
    assert "progression" in result.current_fitness_note


def test_fitness_note_declining(personalizer):
    snap = make_snapshot(fitness_trend="declining")
    result = personalizer.personalize(snap, _profile(), _default_context())
    assert "baisse" in result.current_fitness_note


def test_fitness_note_with_window(personalizer):
    snap = make_snapshot(with_current_window=True)
    result = personalizer.personalize(snap, _profile(), _default_context())
    assert "km/sem" in result.current_fitness_note


def test_race_goal_present(personalizer):
    snap = make_snapshot()
    result = personalizer.personalize(snap, _profile(), _default_context(weeks_to_race=12))
    assert result.has_race_goal is True
    assert result.weeks_to_race == 12


def test_no_race_goal(personalizer):
    snap = make_snapshot()
    result = personalizer.personalize(snap, _profile(), _default_context(weeks_to_race=None))
    assert result.has_race_goal is False
    assert result.weeks_to_race is None


def test_intensity_profile_formatted(personalizer):
    snap = make_snapshot(with_intensity=True)
    result = personalizer.personalize(snap, _profile(), _default_context())
    assert result.intensity_profile is not None
    assert "facile" in result.intensity_profile
    assert "modéré" in result.intensity_profile
    assert "intense" in result.intensity_profile


def test_intensity_profile_none_when_missing(personalizer):
    snap = make_snapshot(with_intensity=False)
    result = personalizer.personalize(snap, _profile(), _default_context())
    assert result.intensity_profile is None


def test_pbs_populated(personalizer):
    snap = make_snapshot()
    result = personalizer.personalize(snap, _profile(), _default_context())
    assert "fastest_pace" in result.relevant_pbs
    assert "longest_run_km" in result.relevant_pbs
    assert "best_week_km" in result.relevant_pbs


def test_race_time_in_pbs_when_provided(personalizer):
    snap = make_snapshot()
    profile = RunnerProfile(
        age=30,
        experience_level_declared="intermediate",
        sessions_per_week_available=4,
        recent_race_time_10k=2700,
    )
    result = personalizer.personalize(snap, profile, _default_context())
    assert "10k_s" in result.relevant_pbs
    assert result.relevant_pbs["10k_s"] == 2700
