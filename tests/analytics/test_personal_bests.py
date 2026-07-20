from datetime import datetime, timezone
from pathlib import Path

from src.analytics.personal_bests import compute_personal_bests
from src.domain.activity import Activity, ActivityMetrics


def _activity(distance_m: float, duration_s: float, dt: datetime, elevation_m: float | None = None) -> Activity:
    return Activity(
        source_file=Path("run.gpx"),
        source_type="GPX",
        date=dt,
        sport_type="running",
        metrics=ActivityMetrics(distance_m=distance_m, duration_s=duration_s, elevation_gain_m=elevation_m),
    )


def _dt(day: int) -> datetime:
    return datetime(2026, 3, day, 8, 0, tzinfo=timezone.utc)


class TestComputePersonalBests:
    def test_empty_returns_none(self):
        assert compute_personal_bests([]) is None

    def test_longest_run(self):
        acts = [
            _activity(5000, 1800, _dt(1)),
            _activity(21000, 7200, _dt(8)),
            _activity(10000, 3600, _dt(15)),
        ]
        pb = compute_personal_bests(acts)
        assert pb.longest_run_km == 21.0

    def test_fastest_pace(self):
        acts = [
            _activity(10000, 3000, _dt(1)),   # 300s/km
            _activity(10000, 3600, _dt(8)),   # 360s/km
        ]
        pb = compute_personal_bests(acts)
        assert pb.fastest_pace_s_per_km == 300.0

    def test_fastest_pace_ignores_short_runs(self):
        acts = [
            _activity(1000, 180, _dt(1)),    # 180s/km — ignoré (<3km)
            _activity(10000, 3600, _dt(8)),  # 360s/km — pris en compte
        ]
        pb = compute_personal_bests(acts)
        assert pb.fastest_pace_s_per_km == 360.0

    def test_most_elevation(self):
        acts = [
            _activity(10000, 3600, _dt(1), elevation_m=50.0),
            _activity(10000, 3600, _dt(8), elevation_m=200.0),
        ]
        pb = compute_personal_bests(acts)
        assert pb.most_elevation_m == 200.0

    def test_best_week(self):
        acts = [
            _activity(10000, 3600, _dt(2)),   # semaine 1 : 10km
            _activity(20000, 7200, _dt(9)),   # semaine 2 : 20km
            _activity(5000, 1800, _dt(11)),   # semaine 2 : +5km → 25km total
        ]
        pb = compute_personal_bests(acts)
        assert pb.best_week_km == 25.0

    def test_elevation_none_when_no_data(self):
        acts = [_activity(10000, 3600, _dt(1), elevation_m=None)]
        pb = compute_personal_bests(acts)
        assert pb.most_elevation_m is None
