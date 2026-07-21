from src.activity_intelligence.classifier import ActivityClassification, classify
from src.activity_intelligence.context import AthleteContext
from src.analytics.pace_trends import PaceTrend, compute_pace_trend
from src.analytics.personal_bests import PersonalBests, compute_personal_bests
from src.analytics.weekly_stats import WeekStats, compute_weekly_stats
from src.database.repository import ActivityRepository
from src.domain.activity import Activity
from src.runner_model.builder import build_snapshot
from src.runner_model.repository import RunnerSnapshotRepository
from src.runner_model.snapshot import RunnerSnapshot


class RunnerIntelligence:
    def __init__(self, repo: ActivityRepository, snapshot_repo: RunnerSnapshotRepository | None = None):
        self._repo = repo
        self._snapshot_repo = snapshot_repo

    def weekly_stats(self) -> list[WeekStats]:
        return compute_weekly_stats(self._activities())

    def pace_trend(self, window_weeks: int = 4) -> PaceTrend | None:
        return compute_pace_trend(self._activities(), window_weeks=window_weeks)

    def personal_bests(self) -> PersonalBests | None:
        return compute_personal_bests(self._activities())

    def athlete_context(self) -> AthleteContext | None:
        return AthleteContext.from_activities(self._activities())

    def classify_activity(self, activity: Activity) -> ActivityClassification | None:
        context = self.athlete_context()
        if context is None:
            return None
        return classify(activity, context)

    def classify_all(self) -> list[tuple[Activity, ActivityClassification]]:
        context = self.athlete_context()
        if context is None:
            return []
        return [(a, classify(a, context)) for a in self._activities()]

    def snapshot(self) -> RunnerSnapshot:
        snap = build_snapshot(self._activities())
        if self._snapshot_repo is not None:
            self._snapshot_repo.save(snap)
        return snap

    def latest_snapshot(self) -> RunnerSnapshot | None:
        if self._snapshot_repo is None:
            return None
        return self._snapshot_repo.get_latest()

    def _activities(self) -> list[Activity]:
        return [a for a in self._repo.get_all() if a.sport_type == "running"]
