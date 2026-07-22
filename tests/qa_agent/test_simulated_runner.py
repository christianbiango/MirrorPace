"""Unit tests for SimulatedRunner — all LLM calls are mocked."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.qa_agent.domain.schemas.runner_profile import RunnerProfile
from src.qa_agent.simulation.simulated_runner import RunnerMessage, SimulatedRunner


@pytest.fixture
def profile() -> RunnerProfile:
    return RunnerProfile(
        id="test_runner",
        display_name="Test Runner",
        system_prompt="Tu es un coureur de test.",
        opening_messages=["analyse ma semaine", "comment s'est passée ma semaine ?"],
        expected_intents=["ANALYSIS_REQUEST"],
    )


@pytest.fixture
def runner(profile) -> SimulatedRunner:
    return SimulatedRunner(profile=profile, api_key="fake-key")


# ── first_message ─────────────────────────────────────────────────────────────

def test_first_message_returns_from_opening_messages(runner, profile):
    for _ in range(20):
        msg = runner.first_message()
        assert msg in profile.opening_messages


def test_first_message_is_deterministic_from_choices(runner, profile):
    messages = {runner.first_message() for _ in range(50)}
    assert messages <= set(profile.opening_messages)


# ── next_message ──────────────────────────────────────────────────────────────

def test_next_message_returns_runner_message(runner):
    payload = '{"message": "pourquoi tu me demandes de réduire ?", "satisfied": false}'
    with patch.object(runner._client, "generate", return_value=payload):
        result = runner.next_message([{"role": "user", "content": "analyse"}])

    assert isinstance(result, RunnerMessage)
    assert result.message == "pourquoi tu me demandes de réduire ?"
    assert result.satisfied is False


def test_next_message_detects_satisfied_true(runner):
    payload = '{"message": "merci, c\'est clair !", "satisfied": true}'
    with patch.object(runner._client, "generate", return_value=payload):
        result = runner.next_message([])

    assert result.satisfied is True
    assert "merci" in result.message


def test_next_message_handles_malformed_json(runner):
    with patch.object(runner._client, "generate", return_value="not json"):
        result = runner.next_message([])

    assert isinstance(result, RunnerMessage)
    assert result.satisfied is False
    assert result.message == "not json"


def test_next_message_handles_missing_keys(runner):
    payload = '{"message": "ok"}'
    with patch.object(runner._client, "generate", return_value=payload):
        result = runner.next_message([])

    assert result.message == "ok"
    assert result.satisfied is False


def test_next_message_passes_history_to_llm(runner):
    history = [
        {"role": "user", "content": "analyse"},
        {"role": "assistant", "content": "voici l'analyse"},
    ]
    payload = '{"message": "pourquoi ?", "satisfied": false}'
    mock_generate = MagicMock(return_value=payload)

    with patch.object(runner._client, "generate", mock_generate):
        runner.next_message(history)

    call_kwargs = mock_generate.call_args
    user_prompt_sent = call_kwargs.kwargs.get("user_prompt") or call_kwargs[0][1]
    assert "analyse" in user_prompt_sent
    assert "voici l'analyse" in user_prompt_sent
