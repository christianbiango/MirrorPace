import gpxpy
from datetime import datetime, timezone
from pathlib import Path

from src.domain.activity import Activity, ActivityMetrics


def _to_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc)
    return dt.replace(tzinfo=timezone.utc)


def parse_gpx(file_path: Path) -> Activity:
    with open(file_path, "r") as f:
        gpx = gpxpy.parse(f)

    if not gpx.tracks:
        raise ValueError(f"No tracks found in {file_path}")

    track = gpx.tracks[0]
    segment = track.segments[0] if track.segments else None

    date = gpx.time
    if date is None and segment and segment.points:
        date = segment.points[0].time
    date = _to_utc(date)

    distance_m = gpx.length_2d() or None

    duration_s = None
    if segment and segment.points and len(segment.points) > 1:
        t_start = segment.points[0].time
        t_end = segment.points[-1].time
        if t_start and t_end:
            duration_s = (t_end - t_start).total_seconds()

    uphill, _ = gpx.get_uphill_downhill()
    elevation_gain_m = uphill if uphill else None

    sport_type = track.type.lower() if track.type else None

    metrics = ActivityMetrics(
        distance_m=distance_m,
        duration_s=duration_s,
        elevation_gain_m=elevation_gain_m,
    )

    return Activity(
        source_file=file_path,
        source_type="GPX",
        date=date,
        sport_type=sport_type,
        metrics=metrics,
        physiology=None,
    )
