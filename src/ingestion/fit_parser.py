import fitparse
from datetime import timezone
from pathlib import Path

from src.domain.activity import Activity, ActivityMetrics, PhysiologyMetrics


def parse_fit(file_path: Path) -> Activity:
    fitfile = fitparse.FitFile(str(file_path))

    for message in fitfile.get_messages("session"):
        data = {m.name: m.value for m in message}

        sport_raw = data.get("sport")
        if sport_raw is not None:
            sport_type = sport_raw.value.lower() if hasattr(sport_raw, "value") else str(sport_raw).lower()
        else:
            sport_type = None

        date = data.get("start_time")
        if date is not None and date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)

        # total_timer_time = moving time (preferred for pace); fallback to elapsed time
        duration_s = data.get("total_timer_time") or data.get("total_elapsed_time")

        metrics = ActivityMetrics(
            distance_m=data.get("total_distance"),
            duration_s=duration_s,
        )

        avg_hr = data.get("avg_heart_rate")
        max_hr = data.get("max_heart_rate")
        physiology = PhysiologyMetrics(avg_hr=avg_hr, max_hr=max_hr) if (avg_hr or max_hr) else None

        return Activity(
            source_file=file_path,
            source_type="FIT",
            date=date,
            sport_type=sport_type,
            metrics=metrics,
            physiology=physiology,
        )

    raise ValueError(f"No session message found in {file_path}")
