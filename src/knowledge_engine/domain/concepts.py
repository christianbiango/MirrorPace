"""Immutable scientific constants — KB v1.2 §4.3.

These values must never leak into `config/thresholds.yaml`; they are facts,
not tunables.
"""

from __future__ import annotations

MARATHON_DISTANCE_KM: float = 42.195
HALF_MARATHON_DISTANCE_KM: float = 21.0975
TEN_K_DISTANCE_KM: float = 10.0
FIVE_K_DISTANCE_KM: float = 5.0

MINUTES_PER_HOUR: float = 60.0
SECONDS_PER_MINUTE: float = 60.0

# Gabbett canonical ACWR windows
ACWR_ACUTE_WINDOW_DAYS: int = 7
ACWR_CHRONIC_WINDOW_DAYS: int = 28

# Riegel (1981)
RIEGEL_DEFAULT_EXPONENT: float = 1.06

# Foster session-RPE requires per-session RPE × per-session duration
# (not computable with the weekly aggregation used in V1).
FOSTER_SESSION_RPE_REQUIRES_PER_SESSION_RPE: bool = True
