from __future__ import annotations

import pytest

from src.knowledge_engine.domain.schemas.runner_state import RunnerProfile
from src.runner_model.profile_store import RunnerProfileStore


@pytest.fixture
def store(tmp_path):
    return RunnerProfileStore(path=tmp_path / "runner_profile.yaml")


def _profile(**overrides) -> RunnerProfile:
    defaults = dict(
        age=23,
        experience_level_declared="intermediate",
        sessions_per_week_available=4,
        sex="male",
    )
    defaults.update(overrides)
    return RunnerProfile(**defaults)


def test_save_then_load_round_trips(store):
    store.save("christian", _profile(years_running=8.0, experience_level_declared="advanced"))

    runner_id, profile = store.load()

    assert runner_id == "christian"
    assert profile.years_running == 8.0
    assert profile.experience_level_declared == "advanced"
    assert profile.age == 23
    assert profile.sex == "male"


def test_save_creates_missing_parent_directories(tmp_path):
    nested_store = RunnerProfileStore(path=tmp_path / "nested" / "runner_profile.yaml")
    nested_store.save("christian", _profile())
    assert nested_store.exists()


def test_save_overwrites_previous_content(store):
    store.save("christian", _profile(years_running=2.0))
    store.save("christian", _profile(years_running=9.0))

    _, profile = store.load()
    assert profile.years_running == 9.0
