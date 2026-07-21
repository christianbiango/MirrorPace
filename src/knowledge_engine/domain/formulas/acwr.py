"""ACWR + chronic load + delta volume — KB v1.2 §2.2."""

from __future__ import annotations

from statistics import mean
from typing import Any


def compute_chronic_load(
    history: list[float],
    current_week_km: float,
    params: dict[str, Any],
) -> tuple[float, bool]:
    """§2.2 — returns (chronic_load_distance, acwr_reliable_pre_gate).

    `acwr_reliable_pre_gate` reflects only the history-length gate; the
    ACWR magnitude vs chronic_load_min_km may still disable it later.
    """
    if not history:
        return current_week_km, False

    window = min(len(history), params["chronic_load_window_weeks"])
    method = params["chronic_load_method"]
    slice_ = history[:window]
    if method == "simple_mean":
        chronic = mean(slice_) if slice_ else current_week_km
    elif method == "ewma":
        alpha = params["ewma_alpha"]
        # EWMA over recent → old; walk from oldest to newest.
        chronic = slice_[-1]
        for value in reversed(slice_[:-1]):
            chronic = alpha * value + (1 - alpha) * chronic
    else:
        raise ValueError(f"Unknown chronic_load_method: {method!r}")

    reliable = len(history) >= params["acwr_min_history_weeks"]
    return chronic, reliable


def compute_acwr(
    current_week_km: float,
    chronic_load: float,
    reliable_pre_gate: bool,
    params: dict[str, Any],
) -> tuple[float | None, bool]:
    """§2.2 — returns (acwr_distance | None, acwr_reliable)."""
    if chronic_load <= params["chronic_load_min_km"]:
        return None, False
    return current_week_km / chronic_load, reliable_pre_gate


def compute_delta_volume_pct(
    current_week_km: float,
    previous_week_km: float,
    params: dict[str, Any],
) -> tuple[float | None, bool]:
    """§2.2 — returns (delta_volume_pct, delta_volume_reliable)."""
    small_threshold = params["small_volume_threshold_km"]
    if previous_week_km < small_threshold:
        divisor = max(previous_week_km, 1)
        pct = (current_week_km - previous_week_km) / divisor * 100
        return pct, False
    pct = (current_week_km - previous_week_km) / previous_week_km * 100
    return pct, True


def compute_delta_long_run_pct(
    long_run_last: float,
    long_run_previous: float | None,
) -> float | None:
    """§2.2 — returns delta_long_run_pct or None if previous is missing/≤0."""
    if long_run_previous is None or long_run_previous <= 0:
        return None
    return (long_run_last - long_run_previous) / long_run_previous * 100


def compute_progression_slope_km_per_week(history: list[float]) -> float:
    """Least-squares slope over the last N weeks (recent → old in input)."""
    if len(history) < 2:
        return 0.0
    y = list(reversed(history))
    n = len(y)
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(y) / n
    num = sum((xs[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    den = sum((xs[i] - x_mean) ** 2 for i in range(n))
    if den == 0:
        return 0.0
    return num / den


def coefficient_of_variation(values: list[float]) -> float:
    """Coefficient of variation (std / mean). Returns +inf if mean is 0."""
    if not values:
        return float("inf")
    m = mean(values)
    if m == 0:
        return float("inf")
    var = sum((v - m) ** 2 for v in values) / len(values)
    return (var**0.5) / m
