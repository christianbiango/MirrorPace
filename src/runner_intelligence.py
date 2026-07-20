from src.analytics.pace_trends import PaceTrend, compute_pace_trend
from src.analytics.personal_bests import PersonalBests, compute_personal_bests
from src.analytics.weekly_stats import WeekStats, compute_weekly_stats
from src.database.repository import ActivityRepository
from src.domain.activity import Activity


class RunnerIntelligence:
    def __init__(self, repo: ActivityRepository):
        self._repo = repo

    def weekly_stats(self) -> list[WeekStats]:
        return compute_weekly_stats(self._activities())

    def pace_trend(self, window_weeks: int = 4) -> PaceTrend | None:
        return compute_pace_trend(self._activities(), window_weeks=window_weeks)

    def personal_bests(self) -> PersonalBests | None:
        return compute_personal_bests(self._activities())

    def _activities(self) -> list[Activity]:
        return [a for a in self._repo.get_all() if a.sport_type == "running"]
