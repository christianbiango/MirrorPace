"""Apply a pending profile correction after explicit user confirmation.

The correction candidate itself is detected by FollowupHandler (LLM-driven);
this handler only resolves the yes/no confirmation and persists the change.
"""

from __future__ import annotations

import unicodedata

from dataclasses import replace

from src.runner_model.profile_store import RunnerProfileStore

_AFFIRMATIVE = {
    "oui", "ouais", "yep", "ok", "okay", "daccord", "vasy",
    "exact", "correct", "confirme", "confirmes",
}
_NEGATIVE = {
    "non", "nan", "annule", "laisse", "faux", "incorrect",
}


def _normalize(text: str) -> str:
    nfd = unicodedata.normalize("NFD", text.lower())
    stripped = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return "".join(c if c.isalnum() or c.isspace() else " " for c in stripped)


class ProfileCorrectionHandler:
    def __init__(self, profile_store: RunnerProfileStore) -> None:
        self._profile_store = profile_store

    def detect_confirmation(self, message: str) -> bool | None:
        """Return True/False for a clear yes/no, None if ambiguous."""
        tokens = set(_normalize(message).split())
        if tokens & _AFFIRMATIVE:
            return True
        if tokens & _NEGATIVE:
            return False
        return None

    def apply(self, runner_id: str, correction: dict):
        """Load the stored profile, apply the correction fields, persist, return it."""
        _, profile = self._profile_store.load()
        updated = replace(profile, **correction)
        self._profile_store.save(runner_id, updated)
        return updated
