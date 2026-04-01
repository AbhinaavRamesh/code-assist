"""Memory file path resolution."""

from __future__ import annotations

import re
from pathlib import Path

from code_assist.config.constants import get_claude_dir


def get_memory_dir(project_root: str) -> Path:
    """Get the project memory directory: ~/.claude/projects/<hash>/memory/."""
    safe_name = re.sub(r"[^\w\-.]", "-", project_root.strip("/\\"))
    return get_claude_dir() / "projects" / safe_name / "memory"


def get_memory_index_path(project_root: str) -> Path:
    """Get MEMORY.md path for a project."""
    return get_memory_dir(project_root) / "MEMORY.md"


def generate_memory_filename(name: str) -> str:
    """Slugify a memory name into a safe filename."""
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    slug = re.sub(r"[\s_]+", "_", slug).strip("_")
    return f"{slug}.md" if slug else "untitled.md"
