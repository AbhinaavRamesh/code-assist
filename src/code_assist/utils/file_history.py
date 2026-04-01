"""File history tracking.

Records file modifications made by tools so the system can report
what changed and when.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import StrEnum


class FileAction(StrEnum):
    """Actions that can be performed on a file."""

    CREATE = "create"
    WRITE = "write"
    EDIT = "edit"
    DELETE = "delete"


@dataclass(slots=True)
class FileHistoryEntry:
    """A single file modification record."""

    path: str
    action: FileAction
    timestamp: float = field(default_factory=time.time)
    tool_use_id: str = ""


class FileHistoryTracker:
    """Tracks file modifications across a session."""

    def __init__(self) -> None:
        self._entries: list[FileHistoryEntry] = []
        self._modified_files: set[str] = set()

    def record(
        self,
        path: str,
        action: FileAction,
        *,
        tool_use_id: str = "",
    ) -> FileHistoryEntry:
        """Record a file modification."""
        entry = FileHistoryEntry(
            path=path,
            action=action,
            tool_use_id=tool_use_id,
        )
        self._entries.append(entry)
        self._modified_files.add(path)
        return entry

    @property
    def entries(self) -> list[FileHistoryEntry]:
        """All recorded entries in chronological order."""
        return list(self._entries)

    @property
    def modified_files(self) -> set[str]:
        """Set of all file paths that have been modified."""
        return set(self._modified_files)

    def get_entries_for(self, path: str) -> list[FileHistoryEntry]:
        """Get all entries for a specific file path."""
        return [e for e in self._entries if e.path == path]

    def clear(self) -> None:
        """Clear all history."""
        self._entries.clear()
        self._modified_files.clear()

    def __len__(self) -> int:
        return len(self._entries)
