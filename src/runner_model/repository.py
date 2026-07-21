from datetime import timezone

from sqlalchemy.orm import Session

from src.database.models import RunnerSnapshotRecord
from src.runner_model.snapshot import FitnessWindow, IntensityDistribution, RunnerSnapshot


class RunnerSnapshotRepository:
    def __init__(self, session: Session):
        self._session = session

    def save(self, snapshot: RunnerSnapshot) -> RunnerSnapshotRecord:
        record = _to_record(snapshot)
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record

    def get_latest(self) -> RunnerSnapshot | None:
        record = (
            self._session.query(RunnerSnapshotRecord)
            .order_by(RunnerSnapshotRecord.computed_at.desc())
            .first()
        )
        return _to_domain(record) if record else None

    def get_history(self) -> list[RunnerSnapshot]:
        records = (
            self._session.query(RunnerSnapshotRecord)
            .order_by(RunnerSnapshotRecord.computed_at.asc())
            .all()
        )
        return [_to_domain(r) for r in records]


def _to_record(s: RunnerSnapshot) -> RunnerSnapshotRecord:
    return RunnerSnapshotRecord(
        computed_at=s.computed_at,
        total_activities=s.total_activities,
        total_distance_km=s.total_distance_km,
        active_since=s.active_since,
        fitness_trend=s.fitness_trend,
        current_avg_weekly_km=s.current_window.avg_weekly_km if s.current_window else None,
        current_avg_pace_s_per_km=s.current_window.avg_pace_s_per_km if s.current_window else None,
        current_sessions=s.current_window.sessions if s.current_window else None,
        avg_pace_s_per_km=s.avg_pace_s_per_km,
        avg_distance_km=s.avg_distance_km,
        intensity_easy_pct=s.intensity.easy_pct if s.intensity else None,
        intensity_moderate_pct=s.intensity.moderate_pct if s.intensity else None,
        intensity_hard_pct=s.intensity.hard_pct if s.intensity else None,
        intensity_unknown_pct=s.intensity.unknown_pct if s.intensity else None,
        longest_run_km=s.longest_run_km,
        fastest_pace_s_per_km=s.fastest_pace_s_per_km,
        best_week_km=s.best_week_km,
    )


def _to_domain(r: RunnerSnapshotRecord) -> RunnerSnapshot:
    computed_at = r.computed_at
    if computed_at.tzinfo is None:
        computed_at = computed_at.replace(tzinfo=timezone.utc)

    current_window = None
    if r.current_avg_weekly_km is not None:
        current_window = FitnessWindow(
            avg_weekly_km=r.current_avg_weekly_km,
            avg_pace_s_per_km=r.current_avg_pace_s_per_km,
            sessions=r.current_sessions,
        )

    intensity = None
    if r.intensity_easy_pct is not None:
        intensity = IntensityDistribution(
            easy_pct=r.intensity_easy_pct,
            moderate_pct=r.intensity_moderate_pct,
            hard_pct=r.intensity_hard_pct,
            unknown_pct=r.intensity_unknown_pct,
        )

    return RunnerSnapshot(
        computed_at=computed_at,
        total_activities=r.total_activities,
        total_distance_km=r.total_distance_km,
        active_since=r.active_since,
        fitness_trend=r.fitness_trend,
        current_window=current_window,
        avg_pace_s_per_km=r.avg_pace_s_per_km,
        avg_distance_km=r.avg_distance_km,
        intensity=intensity,
        longest_run_km=r.longest_run_km,
        fastest_pace_s_per_km=r.fastest_pace_s_per_km,
        best_week_km=r.best_week_km,
    )
