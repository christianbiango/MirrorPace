from datetime import timezone
from pathlib import Path

from sqlalchemy.orm import Session

from src.database.models import ActivityRecord
from src.domain.activity import Activity, ActivityMetrics, PhysiologyMetrics


class ActivityRepository:
    def __init__(self, session: Session):
        self._session = session

    def save(self, activity: Activity) -> ActivityRecord:
        record = _to_record(activity)
        self._session.add(record)
        self._session.commit()
        return record

    def get_all(self) -> list[Activity]:
        records = self._session.query(ActivityRecord).all()
        return [_to_domain(r) for r in records]

    def get_by_id(self, activity_id: int) -> Activity | None:
        record = self._session.get(ActivityRecord, activity_id)
        return _to_domain(record) if record else None

    def exists(self, source_file: Path) -> bool:
        return (
            self._session.query(ActivityRecord)
            .filter_by(source_file=str(source_file))
            .first()
            is not None
        )


def _to_record(activity: Activity) -> ActivityRecord:
    return ActivityRecord(
        source_file=str(activity.source_file),
        source_type=activity.source_type,
        date=activity.date,
        sport_type=activity.sport_type,
        distance_m=activity.metrics.distance_m if activity.metrics else None,
        duration_s=activity.metrics.duration_s if activity.metrics else None,
        elevation_gain_m=activity.metrics.elevation_gain_m if activity.metrics else None,
        avg_hr=activity.physiology.avg_hr if activity.physiology else None,
        max_hr=activity.physiology.max_hr if activity.physiology else None,
    )


def _to_domain(record: ActivityRecord) -> Activity:
    metrics = ActivityMetrics(
        distance_m=record.distance_m,
        duration_s=record.duration_s,
        elevation_gain_m=record.elevation_gain_m,
    )

    physiology = None
    if record.avg_hr is not None or record.max_hr is not None:
        physiology = PhysiologyMetrics(avg_hr=record.avg_hr, max_hr=record.max_hr)

    # SQLite drops timezone info on storage — reattach UTC on read
    date = record.date
    if date is not None and date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)

    return Activity(
        source_file=Path(record.source_file),
        source_type=record.source_type,
        date=date,
        sport_type=record.sport_type,
        metrics=metrics,
        physiology=physiology,
    )
