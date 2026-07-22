"""Unit tests for ConversationRunner — CoachAgent and SimulatedRunner are mocked."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.coach_agent.domain.intent import AgentResponse
from src.qa_agent.domain.schemas.runner_profile import RunnerProfile
from src.qa_agent.simulation.conversation_runner import ConversationRunner
from src.qa_agent.simulation.simulated_runner import RunnerMessage


@pytest.fixture
def profile() -> RunnerProfile:
    return RunnerProfile(
        id="test",
        display_name="Test Runner",
        system_prompt="",
        opening_messages=["analyse ma semaine"],
        expected_intents=["ANALYSIS_REQUEST"],
    )


def _agent_response(text: str = "Voici l'analyse.", turn: int = 1) -> AgentResponse:
    return AgentResponse(
        text=text,
        intent="ANALYSIS_REQUEST",
        session_id="qa-test",
        turn_number=turn,
    )


def _make_coach_mock() -> MagicMock:
    coach = MagicMock()
    coach.ask.return_value = _agent_response()
    coach._session_store = MagicMock()
    coach._session_store._sessions = {}
    return coach


# ── basic run ─────────────────────────────────────────────────────────────────

def test_run_returns_conversation_log(profile):
    coach = _make_coach_mock()
    runner = ConversationRunner(coach_agent=coach, api_key="fake", max_turns=3)

    with patch("src.qa_agent.simulation.conversation_runner.SimulatedRunner") as MockRunner:
        mock_instance = MagicMock()
        mock_instance.first_message.return_value = "analyse ma semaine"
        mock_instance.next_message.return_value = RunnerMessage(message="merci", satisfied=True)
        MockRunner.return_value = mock_instance

        log = runner.run(profile)

    assert log.conversation_id.startswith("qa-")
    assert log.runner_profile.id == "test"
    assert len(log.entries) >= 1


def test_run_stops_when_satisfied(profile):
    coach = _make_coach_mock()
    runner = ConversationRunner(coach_agent=coach, api_key="fake", max_turns=5)

    with patch("src.qa_agent.simulation.conversation_runner.SimulatedRunner") as MockRunner:
        mock_instance = MagicMock()
        mock_instance.first_message.return_value = "analyse"
        mock_instance.next_message.return_value = RunnerMessage(message="ok merci", satisfied=True)
        MockRunner.return_value = mock_instance

        log = runner.run(profile)

    assert log.termination_reason == "satisfied"
    # Only 1 entry: the first message (runner said satisfied on turn 2 attempt)
    assert len(log.entries) == 1


def test_run_stops_at_max_turns(profile):
    coach = _make_coach_mock()
    runner = ConversationRunner(coach_agent=coach, api_key="fake", max_turns=3)

    with patch("src.qa_agent.simulation.conversation_runner.SimulatedRunner") as MockRunner:
        mock_instance = MagicMock()
        mock_instance.first_message.return_value = "analyse"
        mock_instance.next_message.return_value = RunnerMessage(
            message="encore une question", satisfied=False
        )
        MockRunner.return_value = mock_instance

        log = runner.run(profile)

    assert log.termination_reason == "max_turns"
    assert len(log.entries) == 3


def test_run_uses_unique_session_ids(profile):
    coach = _make_coach_mock()
    runner = ConversationRunner(coach_agent=coach, api_key="fake", max_turns=2)

    session_ids = set()

    with patch("src.qa_agent.simulation.conversation_runner.SimulatedRunner") as MockRunner:
        mock_instance = MagicMock()
        mock_instance.first_message.return_value = "analyse"
        mock_instance.next_message.return_value = RunnerMessage(message="ok", satisfied=True)
        MockRunner.return_value = mock_instance

        for _ in range(5):
            log = runner.run(profile)
            session_ids.add(log.conversation_id)

    assert len(session_ids) == 5


def test_run_captures_started_and_ended_at(profile):
    coach = _make_coach_mock()
    runner = ConversationRunner(coach_agent=coach, api_key="fake", max_turns=2)

    with patch("src.qa_agent.simulation.conversation_runner.SimulatedRunner") as MockRunner:
        mock_instance = MagicMock()
        mock_instance.first_message.return_value = "analyse"
        mock_instance.next_message.return_value = RunnerMessage(message="ok", satisfied=True)
        MockRunner.return_value = mock_instance

        log = runner.run(profile)

    assert log.started_at
    assert log.ended_at
    assert log.started_at <= log.ended_at
