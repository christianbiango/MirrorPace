"""`compute_fatigue_trend()` — KB v1.3.1 C-12 (normative definition).

Replaces §2.5 v1.2 which was ambiguous with short history.

Convention:
- `fatigue_score_history` : list[int] ∈ {1..5}
- Index 0  = most recent (week N-1)
- Index -1 = oldest available
- The current-week fatigue_score is NOT in this array.
"""

from __future__ import annotations


def compute_fatigue_trend(history: list[int] | None) -> str:
    if not history or len(history) < 2:
        return "unknown"

    newest = history[0]
    oldest = history[-1]

    if newest < oldest:
        return "improving"  # score dropped → less fatigued
    if newest > oldest:
        return "worsening"  # score rose → more fatigued
    return "stable"
