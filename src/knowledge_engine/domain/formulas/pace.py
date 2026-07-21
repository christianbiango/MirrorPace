"""`target_marathon_pace_min_km` hierarchy — KB v1.2 §2.6.

Priority (stop at the first available):
  1. race_target_time
  2. Riegel from recent half
  3. Riegel from recent 10k
  4. VMA × marathon fraction (by experience level)
  5. null
"""

from __future__ import annotations

from typing import Any

from ...domain.concepts import (
    HALF_MARATHON_DISTANCE_KM,
    MARATHON_DISTANCE_KM,
    MINUTES_PER_HOUR,
    SECONDS_PER_MINUTE,
    TEN_K_DISTANCE_KM,
)


def riegel_predict_marathon_seconds(
    known_time_sec: float,
    known_distance_km: float,
    exponent: float,
) -> float:
    """t2 = t1 * (d2 / d1) ** exponent (Riegel 1981)."""
    return known_time_sec * (MARATHON_DISTANCE_KM / known_distance_km) ** exponent


def compute_target_marathon_pace(
    profile: Any,
    experience_level: str,
    params: dict[str, Any],
) -> tuple[float | None, str, list[str]]:
    """Returns (pace_min_per_km | None, source, warnings)."""
    warnings: list[str] = []
    exponent: float = params["riegel_exponent"]

    # 1. race_target_time
    if profile.race_target_time is not None:
        pace_min_per_km = profile.race_target_time / SECONDS_PER_MINUTE / MARATHON_DISTANCE_KM

        # §2.6 + §1.3 cross-check vs Riegel(half) — 20% gap → warning.
        if profile.recent_race_time_half is not None:
            predicted = riegel_predict_marathon_seconds(
                profile.recent_race_time_half, HALF_MARATHON_DISTANCE_KM, exponent
            )
            gap = abs(predicted - profile.race_target_time) / profile.race_target_time
            if gap > 0.20:
                warnings.append("race_target_unrealistic")

        return pace_min_per_km, "race_target_time", warnings

    # 2. Riegel from recent half
    if profile.recent_race_time_half is not None:
        predicted = riegel_predict_marathon_seconds(
            profile.recent_race_time_half, HALF_MARATHON_DISTANCE_KM, exponent
        )
        pace_min_per_km = predicted / SECONDS_PER_MINUTE / MARATHON_DISTANCE_KM
        return pace_min_per_km, "riegel_from_half", warnings

    # 3. Riegel from recent 10k
    if profile.recent_race_time_10k is not None:
        predicted = riegel_predict_marathon_seconds(
            profile.recent_race_time_10k, TEN_K_DISTANCE_KM, exponent
        )
        pace_min_per_km = predicted / SECONDS_PER_MINUTE / MARATHON_DISTANCE_KM
        return pace_min_per_km, "riegel_from_10k", warnings

    # 4. VMA
    if profile.VMA_kmh is not None:
        fraction = params["vma_marathon_fraction"][experience_level]
        marathon_speed_kmh = profile.VMA_kmh * fraction
        pace_min_per_km = MINUTES_PER_HOUR / marathon_speed_kmh
        return pace_min_per_km, "vma_only", warnings

    # 5. Unavailable
    return None, "unavailable", warnings
