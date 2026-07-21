from __future__ import annotations

import pytest

from src.runner_memory.domain import CoachingDecision, RunnerEvent
from src.runner_memory.indexer import build_runner_context_store
from src.runner_memory.store import MemoryStore


def _decision(runner_id: str = "christian") -> CoachingDecision:
    return CoachingDecision(
        id="d001",
        runner_id=runner_id,
        date="2026-07-06",
        week_start="2026-07-06",
        decision_ref="ref001",
        action="slight_increase",
        primary_reason="beginner low chronic load",
        dominant_rules=["RULE-010"],
        key_metrics_snapshot={"weekly_distance_km": 40.1, "readiness_score": 35},
        expected_outcome="augmentation progressive",
        text="Semaine 2026-07-06 : 40.1km readiness 35/100. Décision: slight_increase. Règles: RULE-010.",
    )


def _event(runner_id: str = "christian") -> RunnerEvent:
    return RunnerEvent(
        id="e001",
        runner_id=runner_id,
        date="2026-05-01",
        event_type="injury",
        description="douleur mollet gauche",
        body_part="calf",
        severity="moderate",
        resolved_date="2026-05-11",
        text="injury calf moderate douleur mollet",
    )


@pytest.fixture
def populated_store(tmp_path):
    store = MemoryStore(memory_dir=tmp_path)
    store.add_decision(_decision())
    store.add_event(_event())
    return store


def test_store_has_expected_doc_count(populated_store):
    vs = build_runner_context_store("christian", populated_store)
    assert len(vs) == 2


def test_empty_memory_returns_empty_store(tmp_path):
    store = MemoryStore(memory_dir=tmp_path)
    vs = build_runner_context_store("christian", store)
    assert len(vs) == 0


def test_decision_doc_is_queryable(populated_store):
    vs = build_runner_context_store("christian", populated_store)
    results = vs.query("slight_increase beginner volume", k=3)
    assert len(results) >= 1
    ids = [doc_id for doc_id, _, _ in results]
    assert any("decision" in i for i in ids)


def test_event_doc_is_queryable(populated_store):
    vs = build_runner_context_store("christian", populated_store)
    results = vs.query("blessure douleur mollet", k=3)
    assert len(results) >= 1
    ids = [doc_id for doc_id, _, _ in results]
    assert any("event" in i for i in ids)


def test_only_indexes_requested_runner(tmp_path):
    store = MemoryStore(memory_dir=tmp_path)
    store.add_decision(_decision(runner_id="christian"))
    store.add_decision(CoachingDecision(
        id="d002", runner_id="other", date="2026-07-06", week_start="2026-07-06",
        decision_ref="r2", action="maintain", primary_reason="stable",
        dominant_rules=[], key_metrics_snapshot={}, expected_outcome="maintien",
        text="maintain stable",
    ))
    vs = build_runner_context_store("christian", store)
    assert len(vs) == 1
