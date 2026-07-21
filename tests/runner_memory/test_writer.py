from __future__ import annotations

import pytest

from src.runner_memory.store import MemoryStore
from src.runner_memory.writer import MemoryWriter


def _make_envelope_and_state():
    from src.runner_model.state_builder import build_runner_state
    from src.runner_model.profile_store import RunnerProfileStore
    from src.knowledge_engine.api import load_default_config, run_engine
    from src.database.connection import build_engine, build_session
    from src.database.repository import ActivityRepository

    engine = build_engine()
    session = build_session(engine)
    activities = ActivityRepository(session).get_all()
    session.close()

    store = RunnerProfileStore()
    runner_id, profile = store.load()

    from datetime import date
    state = build_runner_state(activities, profile, runner_id)
    envelope = run_engine(state, load_default_config())
    return envelope, state


@pytest.fixture
def memory_store(tmp_path):
    return MemoryStore(memory_dir=tmp_path)


def test_writer_creates_decision(memory_store):
    envelope, state = _make_envelope_and_state()
    writer = MemoryWriter(store=memory_store)
    decision = writer.record(envelope, state)

    assert decision.runner_id == state.meta.runner_id
    assert decision.action == envelope.decision.action
    assert decision.week_start == state.meta.week_start_date
    assert len(decision.decision_ref) == 12
    assert len(decision.id) == 12
    assert decision.actual_outcome is None


def test_writer_persists_decision(memory_store):
    envelope, state = _make_envelope_and_state()
    MemoryWriter(store=memory_store).record(envelope, state)
    decisions = memory_store.get_decisions(state.meta.runner_id)
    assert len(decisions) == 1


def test_writer_is_idempotent(memory_store):
    envelope, state = _make_envelope_and_state()
    writer = MemoryWriter(store=memory_store)
    writer.record(envelope, state)
    writer.record(envelope, state)
    assert len(memory_store.get_decisions(state.meta.runner_id)) == 1


def test_writer_captures_dominant_rules(memory_store):
    envelope, state = _make_envelope_and_state()
    decision = MemoryWriter(store=memory_store).record(envelope, state)
    triggered_ids = {r.rule_id for r in envelope.triggered_rules if r.triggered}
    assert set(decision.dominant_rules) == triggered_ids


def test_writer_captures_key_metrics(memory_store):
    envelope, state = _make_envelope_and_state()
    decision = MemoryWriter(store=memory_store).record(envelope, state)
    m = decision.key_metrics_snapshot
    assert "readiness_score" in m
    assert "weekly_distance_km" in m
    assert "fatigue_score" in m
    assert m["readiness_score"] == envelope.readiness.score


def test_writer_text_contains_week_and_action(memory_store):
    envelope, state = _make_envelope_and_state()
    decision = MemoryWriter(store=memory_store).record(envelope, state)
    assert state.meta.week_start_date in decision.text
    assert envelope.decision.action in decision.text
