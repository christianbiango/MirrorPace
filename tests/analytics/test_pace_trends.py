from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.analytics.pace_trends import compute_pace_trend
from src.domain.activity import Activity, ActivityMetrics


def _activity(distance_m: float, duration_s: float, dt: datetime) -> Activity:
    return Activity(
        source_file=Path("run.gpx"),
        source_type="GPX",
        date=dt,
        sport_type="running",
        metrics=ActivityMetrics(distance_m=distance_m, duration_s=duration_s),
    )


def _weeks_ago(n: int) -> datetime:
    return datetime.now(tz=timezone.utc) - timedelta(weeks=n)


class TestComputePaceTrend:
    def test_empty_returns_none(self):
        assert compute_pace_trend([]) is None

    def test_returns_trend_with_data(self):
        acts = [_activity(10000, 3600, _weeks_ago(1))]
        trend = compute_pace_trend(acts)
        assert trend is not None
        assert trend.current_pace_s_per_km == 360.0

    def test_no_previous_when_only_current_window(self):
        acts = [_activity(10000, 3600, _weeks_ago(1))]
        trend = compute_pace_trend(acts)
        assert trend.previous_pace_s_per_km is None
        assert trend.delta_s is None

    def test_improvement_detected(self):
        acts = [
            _activity(10000, 3900, _weeks_ago(6)),   # ancienne allure : 390s/km (lente)
            _activity(10000, 3600, _weeks_ago(1)),   # nouvelle allure : 360s/km (rapide)
        ]
        trend = compute_pace_trend(acts)
        assert trend.delta_s is not None
        assert trend.delta_s < 0
        assert trend.is_improving is True

    def test_regression_detected(self):
        acts = [
            _activity(10000, 3600, _weeks_ago(6)),   # ancienne allure : 360s/km (rapide)
            _activity(10000, 3900, _weeks_ago(1)),   # nouvelle allure : 390s/km (lente)
        ]
        trend = compute_pace_trend(acts)
        assert trend.delta_s is not None
        assert trend.delta_s > 0
        assert trend.is_improving is False

    def test_skips_activities_under_3km(self):
        acts = [
            _activity(2000, 600, _weeks_ago(1)),   # 2km — ignoré
            _activity(10000, 3600, _weeks_ago(2)),  # 10km — pris en compte
        ]
        trend = compute_pace_trend(acts)
        assert trend is not None

    def test_weighted_pace_favors_longer_runs(self):
        # 5km à 300s/km + 10km à 360s/km → allure pondérée ≠ moyenne simple
        acts = [
            _activity(5000, 1500, _weeks_ago(1)),   # 300s/km
            _activity(10000, 3600, _weeks_ago(2)),  # 360s/km
        ]
        trend = compute_pace_trend(acts)
        # allure pondérée = (1500+3600) / (15) = 340s/km
        assert trend.current_pace_s_per_km == pytest.approx(340.0, rel=0.01)


import pytest
