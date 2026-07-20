from datetime import date, datetime, timezone
from pathlib import Path

from src.analytics.weekly_stats import WeekStats, compute_weekly_stats
from src.domain.activity import Activity, ActivityMetrics


def _activity(distance_m: float, duration_s: float, dt: datetime, elevation_m: float | None = None) -> Activity:
    return Activity(
        source_file=Path("run.gpx"),
        source_type="GPX",
        date=dt,
        sport_type="running",
        metrics=ActivityMetrics(distance_m=distance_m, duration_s=duration_s, elevation_gain_m=elevation_m),
    )


def _dt(y, m, d) -> datetime:
    return datetime(y, m, d, 8, 0, tzinfo=timezone.utc)


class TestComputeWeeklyStats:
    def test_empty_returns_empty(self):
        assert compute_weekly_stats([]) == []

    def test_single_activity(self):
        acts = [_activity(10000, 3600, _dt(2026, 3, 2))]
        stats = compute_weekly_stats(acts)
        assert len(stats) == 1
        assert stats[0].distance_km == 10.0
        assert stats[0].sessions == 1

    def test_two_activities_same_week(self):
        acts = [
            _activity(10000, 3600, _dt(2026, 3, 2)),   # lundi
            _activity(5000, 1800, _dt(2026, 3, 4)),    # mercredi
        ]
        stats = compute_weekly_stats(acts)
        assert len(stats) == 1
        assert stats[0].distance_km == 15.0
        assert stats[0].sessions == 2

    def test_two_activities_different_weeks(self):
        acts = [
            _activity(10000, 3600, _dt(2026, 3, 2)),
            _activity(10000, 3600, _dt(2026, 3, 9)),
        ]
        stats = compute_weekly_stats(acts)
        assert len(stats) == 2

    def test_sorted_by_date(self):
        acts = [
            _activity(5000, 1800, _dt(2026, 3, 9)),
            _activity(10000, 3600, _dt(2026, 3, 2)),
        ]
        stats = compute_weekly_stats(acts)
        assert stats[0].week_start < stats[1].week_start

    def test_week_starts_on_monday(self):
        acts = [_activity(10000, 3600, _dt(2026, 3, 4))]  # mercredi
        stats = compute_weekly_stats(acts)
        assert stats[0].week_start == date(2026, 3, 2)  # lundi

    def test_avg_pace_computed(self):
        acts = [_activity(10000, 3600, _dt(2026, 3, 2))]
        stats = compute_weekly_stats(acts)
        assert stats[0].avg_pace_s_per_km == 360.0

    def test_elevation_summed(self):
        acts = [
            _activity(10000, 3600, _dt(2026, 3, 2), elevation_m=50.0),
            _activity(5000, 1800, _dt(2026, 3, 4), elevation_m=30.0),
        ]
        stats = compute_weekly_stats(acts)
        assert stats[0].elevation_m == 80.0

    def test_elevation_none_when_missing(self):
        acts = [_activity(10000, 3600, _dt(2026, 3, 2), elevation_m=None)]
        stats = compute_weekly_stats(acts)
        assert stats[0].elevation_m is None

    def test_skips_activity_without_date(self):
        acts = [
            Activity(source_file=Path("r.gpx"), source_type="GPX", date=None,
                     sport_type="running", metrics=ActivityMetrics(10000, 3600)),
        ]
        assert compute_weekly_stats(acts) == []
