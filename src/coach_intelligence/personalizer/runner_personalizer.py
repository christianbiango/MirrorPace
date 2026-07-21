from __future__ import annotations

from datetime import date

from src.knowledge_engine.api import PlanContext, RunnerProfile
from src.runner_model.snapshot import RunnerSnapshot

from ..domain.schemas.personalization import CommunicationStyle, PersonalizationContext


def _format_pace(pace_s_per_km: float) -> str:
    mins = int(pace_s_per_km) // 60
    secs = int(pace_s_per_km) % 60
    return f"{mins}:{secs:02d}/km"


def _determine_style(snapshot: RunnerSnapshot, profile: RunnerProfile) -> CommunicationStyle:
    if profile.experience_level_declared == "advanced":
        return "technical"
    if profile.years_running is not None and profile.years_running >= 3:
        return "technical"
    if snapshot.total_activities >= 100:
        return "technical"
    return "simple"


def _build_career_context(snapshot: RunnerSnapshot) -> str:
    parts: list[str] = []
    if snapshot.active_since:
        years = (date.today() - snapshot.active_since).days / 365.25
        parts.append(f"{years:.1f} ans de pratique")
    parts.append(f"{snapshot.total_distance_km:.0f} km au total")
    parts.append(f"{snapshot.total_activities} activités")
    return ", ".join(parts)


def _build_fitness_note(snapshot: RunnerSnapshot) -> str:
    labels = {
        "improving": "en progression",
        "stable": "stable",
        "declining": "en baisse",
        "unknown": "non déterminée",
    }
    label = labels.get(snapshot.fitness_trend, "non déterminée")
    note = f"Tendance {label}"
    if snapshot.current_window:
        note += f" — {snapshot.current_window.avg_weekly_km:.0f} km/sem en moyenne (4 sem)"
    return note


class RunnerPersonalizer:
    def personalize(
        self,
        snapshot: RunnerSnapshot,
        profile: RunnerProfile,
        context: PlanContext,
    ) -> PersonalizationContext:
        style = _determine_style(snapshot, profile)
        career_context = _build_career_context(snapshot)
        fitness_note = _build_fitness_note(snapshot)

        intensity_profile: str | None = None
        if snapshot.intensity:
            i = snapshot.intensity
            intensity_profile = (
                f"{i.easy_pct:.0f}% facile, "
                f"{i.moderate_pct:.0f}% modéré, "
                f"{i.hard_pct:.0f}% intense"
            )

        pbs: dict = {}
        if snapshot.fastest_pace_s_per_km:
            pbs["fastest_pace"] = _format_pace(snapshot.fastest_pace_s_per_km)
        if snapshot.longest_run_km:
            pbs["longest_run_km"] = snapshot.longest_run_km
        if snapshot.best_week_km:
            pbs["best_week_km"] = snapshot.best_week_km
        if profile.recent_race_time_10k:
            pbs["10k_s"] = profile.recent_race_time_10k
        if profile.recent_race_time_half:
            pbs["half_marathon_s"] = profile.recent_race_time_half
        if profile.recent_race_time_marathon:
            pbs["marathon_s"] = profile.recent_race_time_marathon

        return PersonalizationContext(
            communication_style=style,
            has_race_goal=context.weeks_to_race is not None,
            weeks_to_race=context.weeks_to_race,
            race_target_time_s=profile.race_target_time,
            career_context=career_context,
            current_fitness_note=fitness_note,
            intensity_profile=intensity_profile,
            relevant_pbs=pbs,
        )
