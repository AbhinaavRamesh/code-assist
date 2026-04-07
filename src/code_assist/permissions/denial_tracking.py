"""Denial tracking for consecutive permission denials.

Tracks how many times in a row a tool has been denied to decide when to
escalate (e.g. suggest switching modes or aborting).
"""

from __future__ import annotations

_ESCALATION_THRESHOLD = 3


class DenialTracker:
    """Track consecutive permission denials."""

    def __init__(self) -> None:
        self._consecutive: int = 0
        self._last_tool: str | None = None

    def record_denial(self, tool_name: str) -> None:
        """Record a denial for *tool_name*."""
        self._consecutive += 1
        self._last_tool = tool_name

    def get_consecutive_denials(self) -> int:
        """Return the number of consecutive denials recorded."""
        return self._consecutive

    def should_escalate(self) -> bool:
        """Return True after 3+ consecutive denials."""
        return self._consecutive >= _ESCALATION_THRESHOLD

    def reset(self) -> None:
        """Reset the denial counter (e.g. after an allow)."""
        self._consecutive = 0
        self._last_tool = None

    @property
    def last_tool(self) -> str | None:
        """The tool name from the most recent denial, or None."""
        return self._last_tool
