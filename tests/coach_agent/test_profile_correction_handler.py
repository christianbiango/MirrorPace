from __future__ import annotations

import pytest

from src.coach_agent.handlers.profile_correction_handler import ProfileCorrectionHandler
from src.knowledge_engine.domain.schemas.runner_state import RunnerProfile
from src.runner_model.profile_store import RunnerProfileStore


@pytest.fixture
def profile_store(tmp_path):
    store = RunnerProfileStore(path=tmp_path / "runner_profile.yaml")
    store.save(
        "christian",
        RunnerProfile(
            age=23,
            experience_level_declared="intermediate",
            sessions_per_week_available=4,
            sex="male",
            years_running=1.0,
        ),
    )
    return store


@pytest.fixture
def handler(profile_store):
    return ProfileCorrectionHandler(profile_store)


# ── detect_confirmation ───────────────────────────────────────────────────────

@pytest.mark.parametrize("message", ["Oui", "ouais vas-y", "Ok exact", "Confirme"])
def test_detects_affirmative(handler, message):
    assert handler.detect_confirmation(message) is True


@pytest.mark.parametrize("message", ["Non", "Non laisse comme ça", "faux"])
def test_detects_negative(handler, message):
    assert handler.detect_confirmation(message) is False


@pytest.mark.parametrize("message", ["Je cours 10km demain", "Et sinon pour mardi ?"])
def test_ambiguous_returns_none(handler, message):
    assert handler.detect_confirmation(message) is None


# ── apply ──────────────────────────────────────────────────────────────────────

def test_apply_persists_correction(handler, profile_store):
    updated = handler.apply("christian", {"years_running": 8.0, "experience_level_declared": "advanced"})

    assert updated.years_running == 8.0
    assert updated.experience_level_declared == "advanced"

    _, reloaded = profile_store.load()
    assert reloaded.years_running == 8.0
    assert reloaded.experience_level_declared == "advanced"


def test_apply_keeps_untouched_fields(handler, profile_store):
    updated = handler.apply("christian", {"years_running": 8.0})
    assert updated.age == 23
    assert updated.sex == "male"
