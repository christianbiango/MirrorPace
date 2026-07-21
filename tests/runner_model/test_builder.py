from datetime import datetime, timezone
from pathlib import Path

from src.domain.activity import Activity, ActivityMetrics
from src.runner_model.builder import build_snapshot


def _activity(distance_m: float, duration_s: float, dt: datetime) -> Activity:
    return Activity(
        source_file=Path("run.gpx"),
        source_type="GPX",
        date=dt,
        sport_type="running",
        metrics=ActivityMetrics(distance_m=distance_m, duration_s=duration_s),
    )


def _dt(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, 8, 0, tzinfo=timezone.utc)


class TestBuildSnapshot:
    def test_empty_activities(self):
        snap = build_snapshot([])
        assert snap.total_activities == 0
        assert snap.total_distance_km == 0.0
        assert snap.active_since is None
        assert snap.fitness_trend == "unknown"
        assert snap.current_window is None

    def test_total_activities(self):
        acts = [
            _activity(10000, 3600, _dt(2026, 1, 1)),
            _activity(5000, 1800, _dt(2026, 1, 8)),
        ]
        snap = build_snapshot(acts)
        assert snap.total_activities == 2

    def test_total_distance_km(self):
        acts = [
            _activity(10000, 3600, _dt(2026, 1, 1)),
            _activity(5000, 1800, _dt(2026, 1, 8)),
        ]
        snap = build_snapshot(acts)
        assert snap.total_distance_km == 15.0

    def test_active_since(self):
        acts = [
            _activity(10000, 3600, _dt(2026, 3, 1)),
            _activity(5000, 1800, _dt(2026, 1, 5)),
        ]
        snap = build_snapshot(acts)
        from datetime import date
        assert snap.active_since == date(2026, 1, 5)

    def test_personal_bests_populated(self):
        acts = [
            _activity(10000, 3600, _dt(2026, 1, 1)),
            _activity(21000, 7200, _dt(2026, 1, 8)),
        ]
        snap = build_snapshot(acts)
        assert snap.longest_run_km == 21.0
        assert snap.fastest_pace_s_per_km is not None

    def test_intensity_distribution_sums_to_100(self):
        acts = [_activity(10000, 3600, _dt(2026, 1, i)) for i in range(1, 6)]
        snap = build_snapshot(acts)
        if snap.intensity:
            total = (
                snap.intensity.easy_pct
                + snap.intensity.moderate_pct
                + snap.intensity.hard_pct
                + snap.intensity.unknown_pct
            )
            assert abs(total - 100.0) < 0.1

    def test_computed_at_is_utc(self):
        snap = build_snapshot([])
        assert snap.computed_at.tzinfo is not None
