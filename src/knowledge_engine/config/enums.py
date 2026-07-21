"""Canonical enums — KB v1.2 §1.7."""

from __future__ import annotations

PAIN_REGION_ENUM: tuple[str, ...] = (
    "achilles",
    "knee",
    "shin",
    "hip",
    "foot",
    "calf",
    "hamstring",
    "quadriceps",
    "lower_back",
    "glute",
    "it_band",
    "ankle",
    "other",
)

PHASE_ENUM: tuple[str, ...] = (
    "general",
    "specific_marathon",
    "taper",
    "return_from_injury",
    "off_season",
)

CRITICAL_PAIN_REGIONS: frozenset[str] = frozenset(
    {"achilles", "knee", "shin", "hip", "foot"}
)

SEX_ENUM: tuple[str, ...] = ("male", "female", "unspecified")

EXPERIENCE_LEVEL_ENUM: tuple[str, ...] = ("beginner", "intermediate", "advanced")

TERRAIN_TYPE_ENUM: tuple[str, ...] = ("road", "trail", "track", "treadmill", "mixed")

PAIN_TREND_ENUM: tuple[str, ...] = ("improving", "stable", "worsening", "unknown")

PAIN_MECHANISM_ENUM: tuple[str, ...] = (
    "acute",
    "chronic",
    "mechanical",
    "overuse",
    "unknown",
)

FATIGUE_TREND_ENUM: tuple[str, ...] = ("improving", "stable", "worsening", "unknown")

ACTION_ENUM: tuple[str, ...] = (
    "deload",
    "decrease",
    "maintain",
    "slight_increase",
    "increase",
)

PRIORITY_ENUM: tuple[str, ...] = ("P0", "P1", "P2", "P3", "P4")

EXPERIENCE_SOURCE_ENUM: tuple[str, ...] = ("declared", "calculated", "reconciled")

PACE_SOURCE_ENUM: tuple[str, ...] = (
    "race_target_time",
    "riegel_from_half",
    "riegel_from_10k",
    "vma_only",
    "unavailable",
)

MEDICAL_REFERRAL_REASON_ENUM: tuple[str | None, ...] = (
    "pain_critical",
    "pain_tendon",
    "known_pathology",
    None,
)
