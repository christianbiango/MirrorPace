from datetime import datetime, timezone
from pathlib import Path

from src.activity_intelligence.classifier import ActivityClassification, classify
from src.activity_intelligence.context import AthleteContext
from src.domain.activity import Activity, ActivityMetrics


def _ctx(avg_pace: float = 360.0, std_pace: float = 60.0, avg_distance_m: float = 10000.0) -> AthleteContext:
    return AthleteContext(
        avg_pace_s_per_km=avg_pace,
        std_pace_s_per_km=std_pace,
        avg_distance_m=avg_distance_m,
        sample_size=10,
    )


def _activity(distance_m: float, duration_s: float) -> Activity:
    return Activity(
        source_file=Path("run.gpx"),
        source_type="GPX",
        date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        sport_type="running",
        metrics=ActivityMetrics(distance_m=distance_m, duration_s=duration_s),
    )


class TestClassifyRunType:
    def test_short_run(self):
        result = classify(_activity(1500, 450), _ctx())
        assert result.run_type == "short"

    def test_standard_run(self):
        # 10km, avg_distance=10km → not long (1.5× = 15km)
        result = classify(_activity(10000, 3600), _ctx())
        assert result.run_type == "standard"

    def test_long_run(self):
        # 16km > 1.5 × 10km = 15km
        result = classify(_activity(16000, 5760), _ctx())
        assert result.run_type == "long_run"

    def test_no_metrics_returns_short(self):
        act = Activity(
            source_file=Path("r.gpx"),
            source_type="GPX",
            date=None,
            sport_type="running",
            metrics=None,
        )
        result = classify(act, _ctx())
        assert result.run_type == "short"
        assert result.intensity == "unknown"


class TestClassifyIntensity:
    # avg=360, std=60 → hard < 300, easy > 420

    def test_hard(self):
        # pace = 280 < 300
        result = classify(_activity(10000, 2800), _ctx())
        assert result.intensity == "hard"

    def test_moderate(self):
        # pace = 360 (avg)
        result = classify(_activity(10000, 3600), _ctx())
        assert result.intensity == "moderate"

    def test_easy(self):
        # pace = 450 > 420
        result = classify(_activity(10000, 4500), _ctx())
        assert result.intensity == "easy"

    def test_no_pace_returns_unknown(self):
        act = Activity(
            source_file=Path("r.gpx"),
            source_type="GPX",
            date=None,
            sport_type="running",
            metrics=ActivityMetrics(distance_m=10000, duration_s=None),
        )
        result = classify(act, _ctx())
        assert result.intensity == "unknown"
