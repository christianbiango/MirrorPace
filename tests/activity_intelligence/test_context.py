from datetime import datetime, timezone
from pathlib import Path

from src.activity_intelligence.context import AthleteContext
from src.domain.activity import Activity, ActivityMetrics


def _activity(distance_m: float, duration_s: float) -> Activity:
    return Activity(
        source_file=Path("run.gpx"),
        source_type="GPX",
        date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        sport_type="running",
        metrics=ActivityMetrics(distance_m=distance_m, duration_s=duration_s),
    )


class TestAthleteContext:
    def test_empty_returns_none(self):
        assert AthleteContext.from_activities([]) is None

    def test_short_runs_excluded(self):
        # Only activities < 3km — all excluded
        acts = [_activity(1000, 300), _activity(2000, 600)]
        assert AthleteContext.from_activities(acts) is None

    def test_sample_size(self):
        acts = [_activity(5000, 1500), _activity(10000, 3600)]
        ctx = AthleteContext.from_activities(acts)
        assert ctx.sample_size == 2

    def test_avg_pace(self):
        # 5km @ 300s/km, 10km @ 360s/km → avg = 330
        acts = [_activity(5000, 1500), _activity(10000, 3600)]
        ctx = AthleteContext.from_activities(acts)
        assert ctx.avg_pace_s_per_km == 330.0

    def test_std_pace_homogeneous(self):
        # All same pace → std = 0
        acts = [_activity(10000, 3600), _activity(10000, 3600)]
        ctx = AthleteContext.from_activities(acts)
        assert ctx.std_pace_s_per_km == 0.0

    def test_avg_distance(self):
        acts = [_activity(5000, 1500), _activity(15000, 5400)]
        ctx = AthleteContext.from_activities(acts)
        assert ctx.avg_distance_m == 10000.0
