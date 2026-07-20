from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.database.connection import build_engine, build_session
from src.database.repository import ActivityRepository
from src.domain.activity import Activity, ActivityMetrics, PhysiologyMetrics


@pytest.fixture
def repo():
    engine = build_engine("sqlite:///:memory:")
    session = build_session(engine)
    return ActivityRepository(session)


def _make_activity(source_file: str = "data/run.fit") -> Activity:
    return Activity(
        source_file=Path(source_file),
        source_type="FIT",
        date=datetime(2026, 7, 12, 8, 0, 0, tzinfo=timezone.utc),
        sport_type="running",
        metrics=ActivityMetrics(distance_m=10000.0, duration_s=3600.0),
        physiology=PhysiologyMetrics(avg_hr=150, max_hr=175),
    )


class TestSave:
    def test_save_returns_record_with_id(self, repo):
        record = repo.save(_make_activity())
        assert record.id is not None

    def test_save_persists_core_fields(self, repo):
        repo.save(_make_activity())
        activities = repo.get_all()
        assert len(activities) == 1
        a = activities[0]
        assert a.source_type == "FIT"
        assert a.sport_type == "running"

    def test_save_persists_metrics(self, repo):
        repo.save(_make_activity())
        a = repo.get_all()[0]
        assert a.metrics is not None
        assert a.metrics.distance_m == 10000.0
        assert a.metrics.duration_s == 3600.0

    def test_save_persists_physiology(self, repo):
        repo.save(_make_activity())
        a = repo.get_all()[0]
        assert a.physiology is not None
        assert a.physiology.avg_hr == 150
        assert a.physiology.max_hr == 175

    def test_save_preserves_utc_date(self, repo):
        repo.save(_make_activity())
        a = repo.get_all()[0]
        assert a.date is not None
        assert a.date.tzinfo == timezone.utc

    def test_save_activity_without_physiology(self, repo):
        activity = Activity(
            source_file=Path("data/run.fit"),
            source_type="FIT",
            date=None,
            sport_type="running",
            metrics=ActivityMetrics(distance_m=5000.0, duration_s=1800.0),
            physiology=None,
        )
        repo.save(activity)
        a = repo.get_all()[0]
        assert a.physiology is None


class TestGetById:
    def test_get_existing(self, repo):
        record = repo.save(_make_activity())
        a = repo.get_by_id(record.id)
        assert a is not None
        assert a.source_type == "FIT"

    def test_get_missing_returns_none(self, repo):
        assert repo.get_by_id(999) is None


class TestExists:
    def test_exists_after_save(self, repo):
        activity = _make_activity("data/run.fit")
        repo.save(activity)
        assert repo.exists(Path("data/run.fit")) is True

    def test_not_exists_before_save(self, repo):
        assert repo.exists(Path("data/never.fit")) is False
