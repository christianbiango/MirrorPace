import math
from dataclasses import dataclass

from src.domain.activity import Activity

MIN_DISTANCE_M = 3000


@dataclass
class AthleteContext:
    avg_pace_s_per_km: float
    std_pace_s_per_km: float
    avg_distance_m: float
    sample_size: int

    @classmethod
    def from_activities(cls, activities: list[Activity]) -> "AthleteContext | None":
        eligible = [
            a for a in activities
            if a.metrics
            and a.metrics.distance_m
            and a.metrics.distance_m >= MIN_DISTANCE_M
            and a.metrics.avg_pace_s_per_km is not None
        ]

        if not eligible:
            return None

        paces = [a.metrics.avg_pace_s_per_km for a in eligible]
        distances = [a.metrics.distance_m for a in eligible]

        avg_pace = sum(paces) / len(paces)
        variance = sum((p - avg_pace) ** 2 for p in paces) / len(paces)
        std_pace = math.sqrt(variance)
        avg_distance = sum(distances) / len(distances)

        return cls(
            avg_pace_s_per_km=avg_pace,
            std_pace_s_per_km=std_pace,
            avg_distance_m=avg_distance,
            sample_size=len(eligible),
        )
