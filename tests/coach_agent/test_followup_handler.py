from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from src.coach_agent.domain.session import ConversationSession
from src.coach_agent.handlers.followup_handler import FollowupHandler
from src.knowledge_engine.domain.schemas.decision import (
    Decision,
    DecisionEnvelope,
    DecisionMeta,
    PlanHint,
    ReadinessOut,
)
from src.knowledge_engine.domain.schemas.runner_state import RunnerProfile
from src.runner_model.profile_store import RunnerProfileStore


class _FakeLLMResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeLLMClient:
    def __init__(self, response_text: str) -> None:
        self._response_text = response_text
        self.last_user_prompt: str | None = None

    def generate(self, system_prompt: str, user_prompt: str):
        self.last_user_prompt = user_prompt
        return _FakeLLMResponse(self._response_text)


def _envelope(**overrides) -> DecisionEnvelope:
    defaults = dict(
        meta=DecisionMeta(
            engine_version="1.3.1", config_hash="x", computed_at="2026-08-24T00:00:00Z", schema_version="1.3.1",
        ),
        decision=Decision(
            action="maintain", delta_pct=0.0, delta_pct_range=(0.0, 0.0), absolute_next_week_target_km=30.0,
        ),
        readiness=ReadinessOut(score=80, confidence_score=80),
    )
    defaults.update(overrides)
    return DecisionEnvelope(**defaults)


def _session(weeks_to_race: int | None = None, envelope: DecisionEnvelope | None = None) -> ConversationSession:
    last_state = (
        SimpleNamespace(
            context=SimpleNamespace(weeks_to_race=weeks_to_race),
            meta=SimpleNamespace(runner_id="christian"),
        )
        if weeks_to_race is not None
        else None
    )
    return ConversationSession(
        session_id="s1",
        created_at=datetime.now(tz=timezone.utc).isoformat(),
        last_envelope=envelope or _envelope(),
        last_state=last_state,
    )


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


def test_no_analysis_yet_returns_default_text(profile_store):
    handler = FollowupHandler(llm_client=_FakeLLMClient("{}"), memory_store=None, profile_store=profile_store)
    text, sources, correction = handler.handle("Pourquoi ?", ConversationSession(
        session_id="s1", created_at=datetime.now(tz=timezone.utc).isoformat(),
    ))
    assert "pas encore analysé" in text
    assert correction is None


def test_returns_no_correction_when_llm_omits_it(profile_store):
    handler = FollowupHandler(
        llm_client=_FakeLLMClient(json.dumps({"text": "Voici pourquoi."})),
        memory_store=None,
        profile_store=profile_store,
    )
    text, sources, correction = handler.handle("Pourquoi cette décision ?", _session())
    assert text == "Voici pourquoi."
    assert correction is None


def test_extracts_valid_profile_correction(profile_store):
    llm_client = _FakeLLMClient(json.dumps({
        "text": "Je note que tu cours depuis 8 ans — je mets à jour ton profil ?",
        "profile_correction": {"years_running": 8.0, "experience_level_declared": "advanced"},
    }))
    handler = FollowupHandler(llm_client=llm_client, memory_store=None, profile_store=profile_store)

    text, sources, correction = handler.handle("En fait je cours depuis 8 ans", _session())

    assert correction == {"years_running": 8.0, "experience_level_declared": "advanced"}
    assert "je mets à jour ton profil" in text
    assert "PROFIL ENREGISTRÉ" in llm_client.last_user_prompt


def test_ignores_correction_matching_stored_profile(profile_store):
    llm_client = _FakeLLMClient(json.dumps({
        "text": "Ok.",
        "profile_correction": {"experience_level_declared": "intermediate"},
    }))
    handler = FollowupHandler(llm_client=llm_client, memory_store=None, profile_store=profile_store)

    _, _, correction = handler.handle("Je suis un coureur intermédiaire", _session())

    assert correction is None


def test_ignores_invalid_experience_level(profile_store):
    llm_client = _FakeLLMClient(json.dumps({
        "text": "Ok.",
        "profile_correction": {"experience_level_declared": "pro"},
    }))
    handler = FollowupHandler(llm_client=llm_client, memory_store=None, profile_store=profile_store)

    _, _, correction = handler.handle("Je suis un coureur pro", _session())

    assert correction is None


# ── plan-building context (grounding for "build me a plan" requests) ─────────

def test_prompt_includes_weeks_to_race_pace_and_plan_skeleton(profile_store):
    envelope = _envelope(
        target_marathon_pace_min_km=4.616666,
        target_marathon_pace_source="race_target_time",
        plan_hints=[
            PlanHint(
                rule_id="RULE-027",
                hint="structure_specific_block",
                reason="Fenêtre courte (10 sem.) mais base suffisante",
                params={"suggested_phases": {"specific": 8, "taper": 2}},
            ),
        ],
    )
    llm_client = _FakeLLMClient(json.dumps({"text": "Voici ton plan."}))
    handler = FollowupHandler(llm_client=llm_client, memory_store=None, profile_store=profile_store)

    handler.handle("Fais-moi un plan", _session(weeks_to_race=10, envelope=envelope))

    prompt = llm_client.last_user_prompt
    assert "Semaines avant la course : 10" in prompt
    assert "4:37/km" in prompt
    assert "8 sem. spécifique" in prompt


def test_prompt_shows_insufficient_data_fallback_without_plan_hints(profile_store):
    llm_client = _FakeLLMClient(json.dumps({"text": "..."}))
    handler = FollowupHandler(llm_client=llm_client, memory_store=None, profile_store=profile_store)

    handler.handle("Fais-moi un plan", _session(weeks_to_race=10))

    prompt = llm_client.last_user_prompt
    assert "Semaines avant la course : 10" in prompt
    assert "aucun pour l'instant" in prompt


def test_prompt_shows_no_target_race_when_weeks_to_race_unset(profile_store):
    llm_client = _FakeLLMClient(json.dumps({"text": "..."}))
    handler = FollowupHandler(llm_client=llm_client, memory_store=None, profile_store=profile_store)

    handler.handle("Pourquoi ?", _session())

    assert "pas de course cible" in llm_client.last_user_prompt
