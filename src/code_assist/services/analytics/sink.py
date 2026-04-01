"""Analytics event sink using OpenTelemetry."""

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsEvent:
    name: str = ""
    timestamp: float = field(default_factory=time.time)
    properties: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None


class AnalyticsSink:
    """Collects and batches analytics events."""

    def __init__(self) -> None:
        self._events: list[AnalyticsEvent] = []
        self._enabled = True

    def log_event(
        self,
        name: str,
        properties: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> None:
        if not self._enabled:
            return
        self._events.append(
            AnalyticsEvent(name=name, properties=properties or {}, session_id=session_id)
        )

    def flush(self) -> list[AnalyticsEvent]:
        events = self._events.copy()
        self._events.clear()
        return events

    def disable(self) -> None:
        self._enabled = False

    @property
    def event_count(self) -> int:
        return len(self._events)


# Global singleton
_sink: AnalyticsSink | None = None


def get_analytics_sink() -> AnalyticsSink:
    global _sink  # noqa: PLW0603
    if _sink is None:
        _sink = AnalyticsSink()
    return _sink


def log_event(
    name: str,
    properties: dict[str, Any] | None = None,
    session_id: str | None = None,
) -> None:
    get_analytics_sink().log_event(name, properties, session_id)
