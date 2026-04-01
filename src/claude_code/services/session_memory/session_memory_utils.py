"""Session-level memory management utilities."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from claude_code.config.constants import get_claude_dir

logger = logging.getLogger(__name__)


@dataclass
class SessionMemoryEntry:
    """A key point extracted from a conversation."""

    content: str = ""
    timestamp: float = field(default_factory=time.time)
    turn_number: int = 0
    importance: str = "normal"  # low, normal, high


@dataclass
class SessionMemory:
    """In-memory session knowledge store."""

    session_id: str = ""
    entries: list[SessionMemoryEntry] = field(default_factory=list)
    _max_entries: int = 100

    def add(self, content: str, *, turn_number: int = 0, importance: str = "normal") -> None:
        """Add a memory entry."""
        self.entries.append(
            SessionMemoryEntry(
                content=content,
                turn_number=turn_number,
                importance=importance,
            )
        )
        # Prune if exceeding max
        if len(self.entries) > self._max_entries:
            # Keep high-importance entries, drop oldest low-importance
            self.entries.sort(
                key=lambda e: (
                    0 if e.importance == "high" else 1 if e.importance == "normal" else 2,
                    -e.timestamp,
                )
            )
            self.entries = self.entries[: self._max_entries]

    def get_context(self, max_entries: int = 20) -> str:
        """Get session memory as context string."""
        recent = sorted(self.entries, key=lambda e: e.timestamp, reverse=True)[
            :max_entries
        ]
        if not recent:
            return ""
        lines = [f"- {e.content}" for e in reversed(recent)]
        return "Session context:\n" + "\n".join(lines)

    def save_to_disk(self, session_dir: Path) -> None:
        """Persist session memory to disk."""
        session_dir.mkdir(parents=True, exist_ok=True)
        path = session_dir / "session_memory.json"
        data = [
            {
                "content": e.content,
                "timestamp": e.timestamp,
                "turn_number": e.turn_number,
                "importance": e.importance,
            }
            for e in self.entries
        ]
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load_from_disk(cls, session_dir: Path, session_id: str = "") -> SessionMemory:
        """Load session memory from disk."""
        path = session_dir / "session_memory.json"
        memory = cls(session_id=session_id)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                for entry in data:
                    memory.entries.append(
                        SessionMemoryEntry(
                            content=entry.get("content", ""),
                            timestamp=entry.get("timestamp", 0),
                            turn_number=entry.get("turn_number", 0),
                            importance=entry.get("importance", "normal"),
                        )
                    )
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load session memory: %s", e)
        return memory
