"""`experience_level` (computed) — KB v1.2 §5.4."""

from __future__ import annotations

from typing import Any

from ...domain.concepts import (
    HALF_MARATHON_DISTANCE_KM,
    MARATHON_DISTANCE_KM,
    TEN_K_DISTANCE_KM,
)

_LEVEL_RANK = {"beginner": 0, "intermediate": 1, "advanced": 2}


def _longest_race_km(profile: Any) -> float:
    """Infer longest race distance completed from recent race times."""
    if profile.recent_race_time_marathon is not None:
        return MARATHON_DISTANCE_KM
    if profile.recent_race_time_half is not None:
        return HALF_MARATHON_DISTANCE_KM
    if profile.recent_race_time_10k is not None:
        return TEN_K_DISTANCE_KM
    return 0.0


def _meets(criteria: dict[str, Any], years: float | None, chronic: float, longest: float) -> bool:
    if chronic < criteria["min_chronic_load_km"]:
        return False
    if longest < criteria["min_longest_race_km"]:
        return False
    if years is not None and years < criteria["min_years_running"]:
        return False
    # Note §1.3 / D-04: if years_running is null → treated as unknown, not a failure.
    return True


def compute_experience_level(
    profile: Any,
    chronic_load_distance: float,
    params: dict[str, Any],
) -> tuple[str, str]:
    """Returns (experience_level, experience_level_source).

    Source values: "declared" | "calculated" | "reconciled".
    """
    criteria = params["experience_level_criteria"]
    years = profile.years_running
    longest = _longest_race_km(profile)

    candidate = "beginner"
    if _meets(criteria["intermediate"], years, chronic_load_distance, longest):
        candidate = "intermediate"
    if _meets(criteria["advanced"], years, chronic_load_distance, longest):
        candidate = "advanced"

    declared = profile.experience_level_declared
    if declared == candidate:
        return candidate, "reconciled"

    if _LEVEL_RANK[declared] > _LEVEL_RANK[candidate]:
        # Declared is more flattering than criteria allow → don't trust it.
        return candidate, "calculated"

    # Declared is more prudent than what criteria would allow → respect it.
    return declared, "declared"
