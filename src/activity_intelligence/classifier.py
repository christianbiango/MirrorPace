from dataclasses import dataclass
from typing import Literal

from src.activity_intelligence.context import MIN_DISTANCE_M, AthleteContext
from src.domain.activity import Activity

RunType = Literal["long_run", "standard", "short"]
Intensity = Literal["easy", "moderate", "hard", "unknown"]

LONG_RUN_FACTOR = 1.5


@dataclass
class ActivityClassification:
    run_type: RunType
    intensity: Intensity


def classify(activity: Activity, context: AthleteContext) -> ActivityClassification:
    metrics = activity.metrics
    if not metrics or not metrics.distance_m:
        return ActivityClassification(run_type="short", intensity="unknown")

    run_type = _classify_run_type(metrics.distance_m, context)
    intensity = _classify_intensity(metrics.avg_pace_s_per_km, context)

    return ActivityClassification(run_type=run_type, intensity=intensity)


def _classify_run_type(distance_m: float, context: AthleteContext) -> RunType:
    if distance_m < MIN_DISTANCE_M:
        return "short"
    if distance_m > context.avg_distance_m * LONG_RUN_FACTOR:
        return "long_run"
    return "standard"


def _classify_intensity(pace_s_per_km: float | None, context: AthleteContext) -> Intensity:
    if pace_s_per_km is None:
        return "unknown"

    # Lower pace = faster = harder
    hard_threshold = context.avg_pace_s_per_km - context.std_pace_s_per_km
    easy_threshold = context.avg_pace_s_per_km + context.std_pace_s_per_km

    if pace_s_per_km < hard_threshold:
        return "hard"
    if pace_s_per_km > easy_threshold:
        return "easy"
    return "moderate"
