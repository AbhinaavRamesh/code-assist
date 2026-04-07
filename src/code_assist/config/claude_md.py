"""CLAUDE.md file discovery and parsing.

CLAUDE.md file discovery and parsing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from code_assist.config.constants import (
    CLAUDE_LOCAL_MD,
    CLAUDE_MD_FILES,
    CLAUDE_RULES_DIR,
    MAX_MEMORY_CHARACTER_COUNT,
    get_managed_claude_rules_dir,
    get_user_claude_rules_dir,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Memory File Info
# ---------------------------------------------------------------------------


@dataclass
class MemoryFileInfo:
    """Information about a discovered CLAUDE.md or rules file."""

    path: str = ""
    content: str = ""
    source: str = ""  # managed, user, project, local
    is_root: bool = False
    relative_path: str | None = None
    size: int = 0
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# File Discovery
# ---------------------------------------------------------------------------


def _find_claude_md_files(directory: Path) -> list[Path]:
    """Find CLAUDE.md files in a directory."""
    found: list[Path] = []
    for pattern in CLAUDE_MD_FILES:
        candidate = directory / pattern
        if candidate.is_file():
            found.append(candidate)
    return found


def _find_rules_files(directory: Path) -> list[Path]:
    """Find .claude/rules/*.md files."""
    rules_dir = directory / CLAUDE_RULES_DIR
    if rules_dir.is_dir():
        return sorted(rules_dir.glob("*.md"))
    return []


def _find_local_claude_md(directory: Path) -> Path | None:
    """Find CLAUDE.local.md in a directory."""
    candidate = directory / CLAUDE_LOCAL_MD
    if candidate.is_file():
        return candidate
    return None


def _read_file_safe(path: Path) -> str:
    """Read a file, returning empty string on error."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        logger.warning("Failed to read %s: %s", path, e)
        return ""


# ---------------------------------------------------------------------------
# Memory File Loading
# ---------------------------------------------------------------------------


def get_memory_files(
    project_root: str | None = None,
    *,
    include_managed: bool = True,
    include_user: bool = True,
    additional_dirs: list[str] | None = None,
) -> list[MemoryFileInfo]:
    """Discover and load all CLAUDE.md and rules files.

    Loading order (lowest to highest priority):
    1. Managed memory (/etc/code-assist/CLAUDE.md)
    2. User memory (~/.claude/CLAUDE.md)
    3. Project memory (CLAUDE.md, .claude/CLAUDE.md, .claude/rules/*.md)
    4. Local memory (CLAUDE.local.md)
    """
    files: list[MemoryFileInfo] = []

    # 1. Managed memory
    if include_managed:
        managed_dir = get_managed_claude_rules_dir()
        for path in _find_claude_md_files(managed_dir):
            content = _read_file_safe(path)
            if content:
                files.append(
                    MemoryFileInfo(
                        path=str(path),
                        content=content,
                        source="managed",
                        size=len(content),
                    )
                )

    # 2. User memory
    if include_user:
        user_dir = get_user_claude_rules_dir()
        for path in _find_claude_md_files(user_dir):
            content = _read_file_safe(path)
            if content:
                files.append(
                    MemoryFileInfo(
                        path=str(path),
                        content=content,
                        source="user",
                        size=len(content),
                    )
                )

    # 3. Project memory (walk up from project root)
    if project_root:
        root = Path(project_root)

        # CLAUDE.md files in project root
        for path in _find_claude_md_files(root):
            content = _read_file_safe(path)
            if content:
                files.append(
                    MemoryFileInfo(
                        path=str(path),
                        content=content,
                        source="project",
                        is_root=True,
                        relative_path=str(path.relative_to(root)),
                        size=len(content),
                    )
                )

        # Rules files
        for path in _find_rules_files(root):
            content = _read_file_safe(path)
            if content:
                files.append(
                    MemoryFileInfo(
                        path=str(path),
                        content=content,
                        source="project",
                        relative_path=str(path.relative_to(root)),
                        size=len(content),
                    )
                )

        # 4. Local memory
        local_path = _find_local_claude_md(root)
        if local_path:
            content = _read_file_safe(local_path)
            if content:
                files.append(
                    MemoryFileInfo(
                        path=str(local_path),
                        content=content,
                        source="local",
                        relative_path=CLAUDE_LOCAL_MD,
                        size=len(content),
                    )
                )

    # Also check additional directories
    if additional_dirs:
        for dir_path in additional_dirs:
            d = Path(dir_path)
            if d.is_dir():
                for path in _find_claude_md_files(d):
                    content = _read_file_safe(path)
                    if content:
                        files.append(
                            MemoryFileInfo(
                                path=str(path),
                                content=content,
                                source="project",
                                size=len(content),
                            )
                        )

    return files


def get_claude_mds(files: list[MemoryFileInfo]) -> list[MemoryFileInfo]:
    """Filter memory files to only CLAUDE.md files (not rules)."""
    return [f for f in files if f.path.endswith("CLAUDE.md")]


def get_large_memory_files(files: list[MemoryFileInfo]) -> list[MemoryFileInfo]:
    """Find memory files that exceed the size limit."""
    return [f for f in files if f.size > MAX_MEMORY_CHARACTER_COUNT]


def build_claude_md_context(files: list[MemoryFileInfo]) -> str:
    """Build the combined CLAUDE.md content for system prompt injection."""
    if not files:
        return ""

    parts: list[str] = []
    for f in files:
        header = f"Contents of {f.path}"
        if f.source == "user":
            header += " (user's private global instructions for all projects)"
        elif f.source == "managed":
            header += " (organization-managed instructions)"
        parts.append(f"{header}:\n\n{f.content}")

    return "\n\n".join(parts)


def is_memory_file_path(file_path: str) -> bool:
    """Check if a file path is a CLAUDE.md or rules file."""
    name = Path(file_path).name
    return (
        name == "CLAUDE.md"
        or name == CLAUDE_LOCAL_MD
        or (CLAUDE_RULES_DIR in file_path and name.endswith(".md"))
    )
