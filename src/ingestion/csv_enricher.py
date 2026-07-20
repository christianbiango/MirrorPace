import pandas as pd
from dataclasses import dataclass
from pathlib import Path

from src.domain.activity import Activity, PhysiologyMetrics

# Column indices in the Strava activities.csv export
_COL_SPORT_TYPE = 3
_COL_FILENAME = 12
_COL_ELEVATION_GAIN = 20

_SPORT_TYPE_MAP = {
    "Course à pied": "running",
    "Vélo": "cycling",
    "Natation": "swimming",
    "Randonnée": "hiking",
    "Marche": "walking",
    "Ski de fond": "nordic_skiing",
    "Ski alpin": "alpine_skiing",
}


@dataclass
class ActivityEnrichment:
    sport_type: str | None = None
    elevation_gain_m: float | None = None


def load_enrichments(csv_path: Path) -> dict[str, ActivityEnrichment]:
    """Returns a map of base filename → enrichment data from Strava activities.csv."""
    df = pd.read_csv(csv_path, header=0)
    enrichments = {}

    for _, row in df.iterrows():
        filename_raw = row.iloc[_COL_FILENAME]
        if pd.isna(filename_raw):
            continue

        filename = Path(str(filename_raw)).name

        sport_raw = row.iloc[_COL_SPORT_TYPE]
        sport_type = _SPORT_TYPE_MAP.get(str(sport_raw)) if pd.notna(sport_raw) else None

        elev_raw = row.iloc[_COL_ELEVATION_GAIN]
        elevation_gain_m = float(elev_raw) if pd.notna(elev_raw) else None

        enrichments[filename] = ActivityEnrichment(
            sport_type=sport_type,
            elevation_gain_m=elevation_gain_m,
        )

    return enrichments


def apply_enrichment(activity: Activity, enrichment: ActivityEnrichment) -> None:
    """Fills None fields with CSV data. Never overwrites existing parsed values."""
    if activity.sport_type is None and enrichment.sport_type:
        activity.sport_type = enrichment.sport_type

    if activity.metrics and activity.metrics.elevation_gain_m is None:
        activity.metrics.elevation_gain_m = enrichment.elevation_gain_m
