"""Unit tests for FeedbackStore."""

from __future__ import annotations

import pytest

from src.coach_agent.domain.feedback import FeedbackEntry
from src.coach_agent.session.feedback_store import FeedbackStore


def _make_entry(
    id: str = "abc001",
    runner_id: str = "christian",
    decision_ref: str | None = "ref001",
) -> FeedbackEntry:
    return FeedbackEntry(
        id=id,
        runner_id=runner_id,
        decision_ref=decision_ref,
        session_id="session-20260722",
        text="C'était trop difficile cette semaine",
        timestamp="2026-07-22T10:00:00+00:00",
    )


@pytest.fixture
def store(tmp_path):
    return FeedbackStore(memory_dir=tmp_path)


def test_add_and_get(store):
    entry = _make_entry()
    assert store.add(entry) is True
    results = store.get_all("christian")
    assert len(results) == 1
    assert results[0].text == "C'était trop difficile cette semaine"
    assert results[0].decision_ref == "ref001"


def test_deduplication(store):
    entry = _make_entry()
    assert store.add(entry) is True
    assert store.add(entry) is False  # same id → no-op
    assert len(store.get_all("christian")) == 1


def test_filters_by_runner_id(store):
    store.add(_make_entry(id="e1", runner_id="christian"))
    store.add(_make_entry(id="e2", runner_id="other"))
    assert len(store.get_all("christian")) == 1
    assert len(store.get_all("other")) == 1


def test_persists_across_instances(tmp_path):
    store1 = FeedbackStore(memory_dir=tmp_path)
    store1.add(_make_entry())

    store2 = FeedbackStore(memory_dir=tmp_path)
    results = store2.get_all("christian")
    assert len(results) == 1
    assert results[0].session_id == "session-20260722"


def test_entry_without_decision_ref(store):
    entry = _make_entry(decision_ref=None)
    store.add(entry)
    results = store.get_all("christian")
    assert results[0].decision_ref is None
