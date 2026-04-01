"""Scanning memory directory for .md files with frontmatter."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from claude_code.memory.memory_types import MemoryEntry, MemoryType
from claude_code.memory.paths import get_memory_dir

logger = logging.getLogger(__name__)

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_memory_frontmatter(content: str) -> dict[str, str]:
    """Parse YAML-like frontmatter from a memory file."""
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def _get_body(content: str) -> str:
    """Extract body content after frontmatter."""
    match = _FRONTMATTER_RE.match(content)
    if match:
        return content[match.end():]
    return content


def scan_memory_files(project_root: str) -> list[MemoryEntry]:
    """Scan the memory directory for .md files and parse them."""
    mem_dir = get_memory_dir(project_root)
    if not mem_dir.exists():
        return []

    entries: list[MemoryEntry] = []
    for path in sorted(mem_dir.glob("*.md")):
        if path.name == "MEMORY.md":
            continue
        try:
            content = path.read_text(encoding="utf-8")
            meta = parse_memory_frontmatter(content)
            body = _get_body(content)
            mem_type_str = meta.get("type", "user")
            try:
                mem_type = MemoryType(mem_type_str)
            except ValueError:
                mem_type = MemoryType.USER

            entries.append(
                MemoryEntry(
                    name=meta.get("name", path.stem),
                    description=meta.get("description", ""),
                    type=mem_type,
                    content=body.strip(),
                    file_path=str(path),
                )
            )
        except OSError as e:
            logger.warning("Failed to read memory file %s: %s", path, e)

    return entries
