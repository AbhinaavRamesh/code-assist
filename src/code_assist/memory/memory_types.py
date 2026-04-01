"""Memory entry types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class MemoryType(StrEnum):
    USER = "user"
    FEEDBACK = "feedback"
    PROJECT = "project"
    REFERENCE = "reference"


@dataclass
class MemoryEntry:
    """A single memory entry with frontmatter metadata."""

    name: str = ""
    description: str = ""
    type: MemoryType = MemoryType.USER
    content: str = ""
    file_path: str = ""
