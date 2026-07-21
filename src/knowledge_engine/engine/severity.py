"""`min_restrictive()` — KB v1.3.1 C-13 (normative)."""

from __future__ import annotations

SEVERITY_ORDER: dict[str, int] = {
    "deload": 5,
    "decrease": 4,
    "maintain": 3,
    "slight_increase": 2,
    "increase": 1,
}


def min_restrictive(action_a: str, action_b: str) -> str:
    """Return the action with the highest severity (most restrictive).

    Used by GF-06 to cap decisions at "maintain" when confidence is low,
    without ever loosening a stricter decision.
    """
    if SEVERITY_ORDER[action_a] >= SEVERITY_ORDER[action_b]:
        return action_a
    return action_b
