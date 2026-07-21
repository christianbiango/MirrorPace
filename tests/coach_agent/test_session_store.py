"""Unit tests for SessionStore and ConversationSession."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.coach_agent.domain.session import ConversationSession, ConversationTurn
from src.coach_agent.session.session_store import SessionStore


@pytest.fixture
def store():
    return SessionStore()


def test_creates_new_session(store):
    session = store.get_or_create("s1")
    assert session.session_id == "s1"
    assert session.turns == []
    assert session.last_envelope is None


def test_returns_same_session_on_second_call(store):
    s1 = store.get_or_create("s1")
    s1.pending_feedback.append("some feedback")
    s2 = store.get_or_create("s1")
    assert s2.pending_feedback == ["some feedback"]


def test_different_session_ids_are_independent(store):
    s1 = store.get_or_create("s1")
    s2 = store.get_or_create("s2")
    s1.pending_feedback.append("x")
    assert store.get_or_create("s2").pending_feedback == []


def test_save_updates_session(store):
    session = store.get_or_create("s1")
    session.turns.append(ConversationTurn(
        turn_number=1,
        role="user",
        text="Analyse ma semaine",
        intent="ANALYSIS_REQUEST",
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
    ))
    store.save(session)
    retrieved = store.get_or_create("s1")
    assert len(retrieved.turns) == 1
    assert retrieved.turns[0].text == "Analyse ma semaine"
