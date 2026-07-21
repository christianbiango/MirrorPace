import gzip
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.domain.activity import Activity, ActivityMetrics
from src.ingestion.fit_parser import parse_fit
from src.ingestion.gpx_parser import parse_gpx
from src.ingestion.parser import parse, is_activity_file

FIT_FILE = Path("data/raw/strava/export_151936996_strava/activities/20398531112.fit.gz")
GPX_FILE = Path("data/raw/strava/export_151936996_strava/activities/18286260719.gpx.gz")


@pytest.fixture
def fit_plain(tmp_path) -> Path:
    dest = tmp_path / "20398531112.fit"
    with gzip.open(FIT_FILE, "rb") as f_in, open(dest, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return dest


@pytest.fixture
def gpx_plain(tmp_path) -> Path:
    dest = tmp_path / "18286260719.gpx"
    with gzip.open(GPX_FILE, "rb") as f_in, open(dest, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return dest


class TestFitParser:
    def test_returns_activity(self):
        assert isinstance(parse_fit(FIT_FILE), Activity)

    def test_source_type(self):
        assert parse_fit(FIT_FILE).source_type == "FIT"

    def test_date_is_utc_aware(self):
        activity = parse_fit(FIT_FILE)
        assert isinstance(activity.date, datetime)
        assert activity.date.tzinfo == timezone.utc

    def test_distance_is_positive(self):
        activity = parse_fit(FIT_FILE)
        assert activity.metrics is not None
        assert activity.metrics.distance_m is not None
        assert activity.metrics.distance_m > 0

    def test_duration_is_positive(self):
        activity = parse_fit(FIT_FILE)
        assert activity.metrics is not None
        assert activity.metrics.duration_s is not None
        assert activity.metrics.duration_s > 0

    def test_source_file_preserved(self):
        assert parse_fit(FIT_FILE).source_file == FIT_FILE

    def test_plain_fit_same_result(self, fit_plain):
        gz = parse_fit(FIT_FILE)
        plain = parse_fit(fit_plain)
        assert plain.metrics.distance_m == gz.metrics.distance_m
        assert plain.date == gz.date


class TestGpxParser:
    def test_returns_activity(self):
        assert isinstance(parse_gpx(GPX_FILE), Activity)

    def test_source_type(self):
        assert parse_gpx(GPX_FILE).source_type == "GPX"

    def test_date_is_utc_aware(self):
        activity = parse_gpx(GPX_FILE)
        assert isinstance(activity.date, datetime)
        assert activity.date.tzinfo == timezone.utc

    def test_distance_is_positive(self):
        activity = parse_gpx(GPX_FILE)
        assert activity.metrics is not None
        assert activity.metrics.distance_m is not None
        assert activity.metrics.distance_m > 0

    def test_duration_is_positive(self):
        activity = parse_gpx(GPX_FILE)
        assert activity.metrics is not None
        assert activity.metrics.duration_s is not None
        assert activity.metrics.duration_s > 0

    def test_source_file_preserved(self):
        assert parse_gpx(GPX_FILE).source_file == GPX_FILE

    def test_plain_gpx_same_result(self, gpx_plain):
        gz = parse_gpx(GPX_FILE)
        plain = parse_gpx(gpx_plain)
        assert plain.metrics.distance_m == gz.metrics.distance_m
        assert plain.date == gz.date


class TestDispatcher:
    def test_routes_fit_gz(self):
        assert parse(FIT_FILE).source_type == "FIT"

    def test_routes_gpx_gz(self):
        assert parse(GPX_FILE).source_type == "GPX"

    def test_routes_plain_fit(self, fit_plain):
        assert parse(fit_plain).source_type == "FIT"

    def test_routes_plain_gpx(self, gpx_plain):
        assert parse(gpx_plain).source_type == "GPX"

    def test_unsupported_format_raises(self):
        with pytest.raises(ValueError, match="Unsupported format"):
            parse(Path("activity.csv"))


class TestIsActivityFile:
    def test_fit(self):
        assert is_activity_file(Path("run.fit")) is True

    def test_gpx(self):
        assert is_activity_file(Path("run.gpx")) is True

    def test_fit_gz(self):
        assert is_activity_file(Path("run.fit.gz")) is True

    def test_gpx_gz(self):
        assert is_activity_file(Path("run.gpx.gz")) is True

    def test_csv(self):
        assert is_activity_file(Path("activities.csv")) is False

    def test_gz_unknown_inner(self):
        assert is_activity_file(Path("file.csv.gz")) is False


class TestActivityMetricsPace:
    def test_pace_computed_from_fit(self):
        activity = parse_fit(FIT_FILE)
        if activity.metrics and activity.metrics.distance_m and activity.metrics.duration_s:
            assert activity.metrics.avg_pace_s_per_km > 0

    def test_pace_none_when_no_distance(self):
        metrics = ActivityMetrics(distance_m=None, duration_s=3600)
        assert metrics.avg_pace_s_per_km is None
