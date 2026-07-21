from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FeedbackEntry:
    id: str               # sha256[:12] of runner_id + decision_ref + timestamp
    runner_id: str
    decision_ref: str | None   # None if no prior analysis in session
    session_id: str
    text: str
    timestamp: str        # ISO-8601
