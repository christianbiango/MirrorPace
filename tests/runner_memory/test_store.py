from __future__ import annotations

import pytest

from src.runner_memory.domain import CoachingDecision, RunnerEvent
from src.runner_memory.store import MemoryStore


def _make_decision(id: str = "abc123", runner_id: str = "christian") -> CoachingDecision:
    return CoachingDecision(
        id=id,
        runner_id=runner_id,
        date="2026-07-06",
        week_start="2026-07-06",
        decision_ref="ref001",
        action="slight_increase",
        primary_reason="beginner low load",
        dominant_rules=["RULE-010", "RULE-016"],
        key_metrics_snapshot={"weekly_distance_km": 40.1, "readiness_score": 35},
        expected_outcome="augmentation progressive",
        text="Semaine 2026-07-06 : 40.1km readiness 35/100.",
    )


def _make_event(id: str = "evt001", runner_id: str = "christian") -> RunnerEvent:
    return RunnerEvent(
        id=id,
        runner_id=runner_id,
        date="2026-05-01",
        event_type="injury",
        description="douleur mollet gauche",
        body_part="calf",
        severity="moderate",
        resolved_date="2026-05-11",
        text="injury calf moderate douleur mollet 2026-05-01",
    )


@pytest.fixture
def store(tmp_path):
    return MemoryStore(memory_dir=tmp_path)


def test_add_and_get_decision(store):
    d = _make_decision()
    assert store.add_decision(d) is True
    decisions = store.get_decisions("christian")
    assert len(decisions) == 1
    assert decisions[0].action == "slight_increase"
    assert decisions[0].dominant_rules == ["RULE-010", "RULE-016"]


def test_add_decision_deduplicates(store):
    d = _make_decision()
    store.add_decision(d)
    result = store.add_decision(d)
    assert result is False
    assert len(store.get_decisions("christian")) == 1


def test_get_decisions_filters_by_runner(store):
    store.add_decision(_make_decision(id="d1", runner_id="christian"))
    store.add_decision(_make_decision(id="d2", runner_id="other"))
    assert len(store.get_decisions("christian")) == 1
    assert len(store.get_decisions("other")) == 1


def test_add_and_get_event(store):
    e = _make_event()
    assert store.add_event(e) is True
    events = store.get_events("christian")
    assert len(events) == 1
    assert events[0].body_part == "calf"
    assert events[0].severity == "moderate"
    assert events[0].resolved_date == "2026-05-11"


def test_add_event_deduplicates(store):
    e = _make_event()
    store.add_event(e)
    assert store.add_event(e) is False


def test_store_persists_across_instances(tmp_path):
    s1 = MemoryStore(memory_dir=tmp_path)
    s1.add_decision(_make_decision())
    s2 = MemoryStore(memory_dir=tmp_path)
    assert len(s2.get_decisions("christian")) == 1


def test_empty_store_returns_empty_lists(store):
    assert store.get_decisions("christian") == []
    assert store.get_events("christian") == []


def test_key_metrics_snapshot_roundtrip(store):
    d = _make_decision()
    store.add_decision(d)
    loaded = store.get_decisions("christian")[0]
    assert loaded.key_metrics_snapshot["weekly_distance_km"] == 40.1
    assert loaded.key_metrics_snapshot["readiness_score"] == 35
