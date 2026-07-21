"""Input validation — KB v1.2 §1.8 + v1.3 §4.3 additions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime

from ..config.enums import (
    EXPERIENCE_LEVEL_ENUM,
    PAIN_REGION_ENUM,
    PAIN_TREND_ENUM,
    PHASE_ENUM,
    SEX_ENUM,
    TERRAIN_TYPE_ENUM,
)
from ..domain.schemas.runner_state import PainRegion, RunnerState

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)
    pathologies_flagged: bool = False

    def ok(self) -> bool:
        return not self.errors


def _parse_date(value: str) -> date:
    if "T" in value:
        return datetime.fromisoformat(value).date()
    return date.fromisoformat(value)


def _validate_meta(state: RunnerState, report: ValidationReport) -> None:
    meta = state.meta
    if not meta.runner_id:
        report.errors.append("meta.runner_id: required")
    if not _ISO_DATE_RE.match(meta.week_start_date):
        report.errors.append("meta.week_start_date: not an ISO date")
    if not meta.submitted_at:
        report.errors.append("meta.submitted_at: required")
    if meta.week_start_date and meta.submitted_at:
        try:
            submitted = _parse_date(meta.submitted_at)
            week_start = _parse_date(meta.week_start_date)
        except ValueError:
            report.errors.append("meta.dates: unparseable ISO-8601")
            return
        if week_start > submitted:
            report.errors.append("meta.week_start_date: after submitted_at")


def _validate_profile(state: RunnerState, report: ValidationReport) -> None:
    profile = state.profile

    if not (14 <= profile.age <= 90):
        report.errors.append("profile.age: out of [14..90]")

    if profile.sex not in SEX_ENUM:
        report.errors.append(f"profile.sex: not in {SEX_ENUM}")

    if profile.experience_level_declared not in EXPERIENCE_LEVEL_ENUM:
        report.errors.append("profile.experience_level_declared: invalid enum")

    if not (1 <= profile.sessions_per_week_available <= 14):
        report.errors.append("profile.sessions_per_week_available: out of [1..14]")

    if profile.recent_race_time_10k is not None and not (
        1200 <= profile.recent_race_time_10k <= 7200
    ):
        report.errors.append("profile.recent_race_time_10k: out of [1200..7200]")

    if profile.recent_race_time_half is not None and not (
        2700 <= profile.recent_race_time_half <= 18000
    ):
        report.errors.append("profile.recent_race_time_half: out of [2700..18000]")

    if profile.recent_race_time_marathon is not None and not (
        7200 <= profile.recent_race_time_marathon <= 36000
    ):
        report.errors.append("profile.recent_race_time_marathon: out of [7200..36000]")

    if profile.VMA_kmh is not None and not (8 <= profile.VMA_kmh <= 25):
        report.errors.append("profile.VMA_kmh: out of [8..25]")

    if profile.race_target_time is not None and not (
        7200 <= profile.race_target_time <= 36000
    ):
        report.errors.append("profile.race_target_time: out of [7200..36000]")

    # Cross-field warnings
    if profile.pathologies_connues:
        report.pathologies_flagged = True
        report.warnings.append("medical_referral_recommended")


def _validate_pain_region(pr: PainRegion, idx: int, report: ValidationReport) -> None:
    if pr.region not in PAIN_REGION_ENUM:
        report.errors.append(f"week.pain_regions[{idx}].region: invalid enum")
    if pr.intensity not in {0, 1, 2, 3, 4, 5}:
        report.errors.append(f"week.pain_regions[{idx}].intensity: not in {{0..5}}")
    if not (0 <= pr.days_persistent <= 365):
        report.errors.append(f"week.pain_regions[{idx}].days_persistent: out of range")
    if pr.pain_trend not in PAIN_TREND_ENUM:
        report.errors.append(f"week.pain_regions[{idx}].pain_trend: invalid enum")


def _validate_week(state: RunnerState, params: dict, report: ValidationReport) -> None:
    week = state.week

    if not (0 <= week.weekly_distance_km <= 300):
        report.errors.append("week.weekly_distance_km: out of [0..300]")
    if not (0 <= week.previous_week_distance_km <= 300):
        report.errors.append("week.previous_week_distance_km: out of [0..300]")
    if not (0 <= week.weekly_duration_min <= 1800):
        report.errors.append("week.weekly_duration_min: out of [0..1800]")

    if any(v < 0 for v in week.weekly_distance_history):
        report.errors.append("week.weekly_distance_history: negative entry")
    if len(week.weekly_distance_history) > 8:
        report.errors.append("week.weekly_distance_history: >8 entries")

    if week.long_run_km_last_week < 0 or week.long_run_km_last_week > 300:
        report.errors.append("week.long_run_km_last_week: out of [0..300]")
    if week.long_run_km_last_week > week.weekly_distance_km:
        report.errors.append("invalid_long_run")

    if week.long_run_km_previous_week is not None and not (
        0 <= week.long_run_km_previous_week <= 300
    ):
        report.errors.append("week.long_run_km_previous_week: out of [0..300]")

    if week.avg_weekly_RPE is not None and not (0 <= week.avg_weekly_RPE <= 10):
        report.errors.append("week.avg_weekly_RPE: out of [0..10]")

    if week.fatigue_score not in {1, 2, 3, 4, 5}:
        report.errors.append("week.fatigue_score: not in {1..5}")
    if week.sleep_quality_score not in {1, 2, 3, 4, 5}:
        report.errors.append("week.sleep_quality_score: not in {1..5}")

    if not (0 <= week.days_since_last_run <= 365):
        report.errors.append("week.days_since_last_run: out of [0..365]")

    if len(week.pain_regions) > 10:
        report.errors.append("week.pain_regions: >10 entries")
    for idx, pr in enumerate(week.pain_regions):
        _validate_pain_region(pr, idx, report)

    if len(week.session_notes) > 2000:
        report.errors.append("week.session_notes: >2000 chars")

    # v1.3 C-04 — fatigue_score_history schema check
    for i, v in enumerate(week.fatigue_score_history):
        if v not in {1, 2, 3, 4, 5}:
            report.errors.append(f"week.fatigue_score_history[{i}]: not in {{1..5}}")
    if len(week.fatigue_score_history) > 8:
        report.errors.append("week.fatigue_score_history: >8 entries")

    # v1.3 C-06 — implicit speed sanity
    max_speed = params["max_implicit_speed_kmh"]
    if week.weekly_duration_min > 0:
        implicit_kmh = week.weekly_distance_km / (week.weekly_duration_min / 60.0)
        if implicit_kmh > max_speed:
            report.errors.append("invalid_speed_ratio")

    # Warnings
    if len(week.weekly_distance_history) < 4:
        report.warnings.append("acwr_unreliable_short_history")
    if week.avg_weekly_RPE is None:
        report.warnings.append("missing_rpe")

    if week.weekly_distance_km == 0:
        report.info.append("zero_volume_week")


def _validate_context(state: RunnerState, report: ValidationReport) -> None:
    ctx = state.context

    if ctx.current_phase not in PHASE_ENUM:
        report.errors.append("context.current_phase: invalid enum")

    if ctx.weeks_to_race is not None and not (0 <= ctx.weeks_to_race <= 52):
        report.errors.append("context.weeks_to_race: out of [0..52]")

    if ctx.weeks_since_last_injury is not None and not (
        0 <= ctx.weeks_since_last_injury <= 520
    ):
        report.errors.append("context.weeks_since_last_injury: out of [0..520]")

    if ctx.terrain_type not in TERRAIN_TYPE_ENUM:
        report.errors.append("context.terrain_type: invalid enum")

    if ctx.mood_motivation_score is not None and ctx.mood_motivation_score not in {
        1,
        2,
        3,
        4,
        5,
    }:
        report.errors.append("context.mood_motivation_score: not in {1..5}")

    # v1.3 C-08 — return_from_injury without weeks_since_last_injury
    if ctx.current_phase == "return_from_injury" and ctx.weeks_since_last_injury is None:
        report.warnings.append("missing_injury_context")


def _validate_race_target_date(state: RunnerState, report: ValidationReport) -> None:
    """v1.3 C-11 — race_target_date in the past → warning + force weeks_to_race=None."""
    if state.profile.race_target_date is None:
        return
    try:
        target = _parse_date(state.profile.race_target_date)
        week_start = _parse_date(state.meta.week_start_date)
    except ValueError:
        report.errors.append("profile.race_target_date: unparseable ISO date")
        return
    if target < week_start:
        report.warnings.append("race_target_date_in_past")
        state.context.weeks_to_race = None  # force None per spec


def _validate_at_least_one_pace_source(
    state: RunnerState, report: ValidationReport
) -> None:
    """§1.3 — at least one among 10k, half, VMA → else null pace, no error."""
    if (
        state.profile.recent_race_time_10k is None
        and state.profile.recent_race_time_half is None
        and state.profile.VMA_kmh is None
    ):
        report.info.append("no_pace_source_provided")


def validate(state: RunnerState, params: dict) -> ValidationReport:
    """Full validation — mutates state where the spec mandates (race_target_date_in_past)."""
    report = ValidationReport()

    _validate_meta(state, report)
    _validate_profile(state, report)
    _validate_week(state, params, report)
    _validate_context(state, report)
    _validate_race_target_date(state, report)
    _validate_at_least_one_pace_source(state, report)

    return report


class ValidationError(Exception):
    def __init__(self, report: ValidationReport):
        self.report = report
        super().__init__("; ".join(report.errors))
