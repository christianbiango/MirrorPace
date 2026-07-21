from datetime import date, datetime, timezone

import pytest

from src.database.connection import build_engine, build_session
from src.runner_model.repository import RunnerSnapshotRepository
from src.runner_model.snapshot import FitnessWindow, IntensityDistribution, RunnerSnapshot


def _snapshot(computed_at: datetime, total_activities: int = 10) -> RunnerSnapshot:
    return RunnerSnapshot(
        computed_at=computed_at,
        total_activities=total_activities,
        total_distance_km=100.0,
        active_since=date(2025, 1, 1),
        fitness_trend="improving",
        current_window=FitnessWindow(avg_weekly_km=30.0, avg_pace_s_per_km=360.0, sessions=3),
        avg_pace_s_per_km=370.0,
        avg_distance_km=10.0,
        intensity=IntensityDistribution(easy_pct=20.0, moderate_pct=70.0, hard_pct=10.0, unknown_pct=0.0),
        longest_run_km=21.0,
        fastest_pace_s_per_km=300.0,
        best_week_km=60.0,
    )


@pytest.fixture
def repo():
    engine = build_engine("sqlite:///:memory:")
    session = build_session(engine)
    return RunnerSnapshotRepository(session)


class TestSave:
    def test_save_returns_record_with_id(self, repo):
        snap = _snapshot(datetime(2026, 1, 1, tzinfo=timezone.utc))
        record = repo.save(snap)
        assert record.id is not None

    def test_save_persists_core_fields(self, repo):
        snap = _snapshot(datetime(2026, 1, 1, tzinfo=timezone.utc), total_activities=42)
        repo.save(snap)
        result = repo.get_latest()
        assert result.total_activities == 42
        assert result.total_distance_km == 100.0
        assert result.active_since == date(2025, 1, 1)

    def test_save_persists_fitness_trend(self, repo):
        snap = _snapshot(datetime(2026, 1, 1, tzinfo=timezone.utc))
        repo.save(snap)
        assert repo.get_latest().fitness_trend == "improving"

    def test_save_persists_current_window(self, repo):
        snap = _snapshot(datetime(2026, 1, 1, tzinfo=timezone.utc))
        repo.save(snap)
        w = repo.get_latest().current_window
        assert w is not None
        assert w.avg_weekly_km == 30.0
        assert w.avg_pace_s_per_km == 360.0
        assert w.sessions == 3

    def test_save_persists_intensity(self, repo):
        snap = _snapshot(datetime(2026, 1, 1, tzinfo=timezone.utc))
        repo.save(snap)
        i = repo.get_latest().intensity
        assert i is not None
        assert i.easy_pct == 20.0
        assert i.moderate_pct == 70.0
        assert i.hard_pct == 10.0

    def test_save_persists_personal_bests(self, repo):
        snap = _snapshot(datetime(2026, 1, 1, tzinfo=timezone.utc))
        repo.save(snap)
        result = repo.get_latest()
        assert result.longest_run_km == 21.0
        assert result.fastest_pace_s_per_km == 300.0
        assert result.best_week_km == 60.0

    def test_save_preserves_utc(self, repo):
        dt = datetime(2026, 6, 15, 10, 30, tzinfo=timezone.utc)
        repo.save(_snapshot(dt))
        result = repo.get_latest()
        assert result.computed_at.tzinfo is not None
        assert result.computed_at.replace(tzinfo=None) == dt.replace(tzinfo=None)

    def test_save_with_none_fields(self, repo):
        snap = RunnerSnapshot(
            computed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            total_activities=0,
            total_distance_km=0.0,
            active_since=None,
            fitness_trend="unknown",
            current_window=None,
            avg_pace_s_per_km=None,
            avg_distance_km=None,
            intensity=None,
            longest_run_km=None,
            fastest_pace_s_per_km=None,
            best_week_km=None,
        )
        repo.save(snap)
        result = repo.get_latest()
        assert result.current_window is None
        assert result.intensity is None
        assert result.longest_run_km is None


class TestGetLatest:
    def test_returns_none_when_empty(self, repo):
        assert repo.get_latest() is None

    def test_returns_most_recent(self, repo):
        repo.save(_snapshot(datetime(2026, 1, 1, tzinfo=timezone.utc), total_activities=1))
        repo.save(_snapshot(datetime(2026, 6, 1, tzinfo=timezone.utc), total_activities=99))
        result = repo.get_latest()
        assert result.total_activities == 99


class TestGetHistory:
    def test_returns_empty_list_when_no_snapshots(self, repo):
        assert repo.get_history() == []

    def test_returns_all_snapshots_ordered(self, repo):
        repo.save(_snapshot(datetime(2026, 3, 1, tzinfo=timezone.utc), total_activities=20))
        repo.save(_snapshot(datetime(2026, 1, 1, tzinfo=timezone.utc), total_activities=10))
        repo.save(_snapshot(datetime(2026, 6, 1, tzinfo=timezone.utc), total_activities=30))
        history = repo.get_history()
        assert len(history) == 3
        assert history[0].total_activities == 10
        assert history[1].total_activities == 20
        assert history[2].total_activities == 30
