from src.activity_intelligence.classifier import ActivityClassification, classify
from src.activity_intelligence.context import AthleteContext
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

    def _activities(self) -> list[Activity]:
        return [a for a in self._repo.get_all() if a.sport_type == "running"]
