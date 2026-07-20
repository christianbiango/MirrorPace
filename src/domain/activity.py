from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ActivityMetrics:
    distance_m: float | None
    duration_s: float | None
    elevation_gain_m: float | None = None

    @property
    def avg_pace_s_per_km(self) -> float | None:
        if self.distance_m and self.duration_s and self.distance_m > 0:
            return self.duration_s / (self.distance_m / 1000)
        return None


@dataclass
class PhysiologyMetrics:
    avg_hr: int | None
    max_hr: int | None = None


@dataclass
class Activity:
    source_file: Path
    source_type: str           # "FIT" | "GPX"
    date: datetime | None      # Always UTC-aware when set
    sport_type: str | None
    metrics: ActivityMetrics | None = None
    physiology: PhysiologyMetrics | None = None
