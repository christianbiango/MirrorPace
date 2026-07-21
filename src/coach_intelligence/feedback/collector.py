from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class FeedbackCollector(Protocol):
    """Placeholder interface — future Coach Agent will implement feedback persistence."""

    def record(
        self,
        response_ref: str,
        useful: bool | None = None,
        followed: bool | None = None,
        satisfaction: int | None = None,
    ) -> None:
        ...


class NullFeedbackCollector:
    """No-op implementation for use when feedback collection is not configured."""

    def record(self, response_ref: str, **_kwargs: object) -> None:
        pass
