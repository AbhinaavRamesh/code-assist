"""MEMORY.md index file management."""

from __future__ import annotations

import logging
from pathlib import Path

from code_assist.memory.paths import get_memory_dir, get_memory_index_path

logger = logging.getLogger(__name__)

MAX_MEMORY_INDEX_LINES = 200
MAX_MEMORY_INDEX_SIZE = 25_000  # bytes


def read_memory_index(project_root: str) -> str:
    """Read MEMORY.md, truncating to MAX_MEMORY_INDEX_LINES."""
    path = get_memory_index_path(project_root)
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        if len(lines) > MAX_MEMORY_INDEX_LINES:
            lines = lines[:MAX_MEMORY_INDEX_LINES]
            return "".join(lines)
        return text
    except OSError as e:
        logger.warning("Failed to read MEMORY.md: %s", e)
        return ""


def write_memory_index(project_root: str, content: str) -> None:
    """Write MEMORY.md, ensuring directory exists."""
    path = get_memory_index_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def add_memory_to_index(
    project_root: str, title: str, filename: str, description: str
) -> None:
    """Add a memory entry to MEMORY.md."""
    current = read_memory_index(project_root)
    entry = f"- [{title}]({filename}) — {description}\n"
    new_content = current.rstrip("\n") + "\n" + entry if current.strip() else entry
    write_memory_index(project_root, new_content)


def remove_memory_from_index(project_root: str, filename: str) -> None:
    """Remove a memory entry from MEMORY.md by filename."""
    current = read_memory_index(project_root)
    if not current:
        return
    lines = current.splitlines(keepends=True)
    filtered = [line for line in lines if filename not in line]
    write_memory_index(project_root, "".join(filtered))
