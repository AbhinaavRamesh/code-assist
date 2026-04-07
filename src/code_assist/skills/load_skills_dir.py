"""Discover skills from ~/.claude/skills/."""

from __future__ import annotations

import logging
from pathlib import Path

from code_assist.config.constants import get_skills_dir

logger = logging.getLogger(__name__)


def load_skills(
    skills_dir: Path | None = None,
) -> list[dict]:
    """Load skill definitions from the skills directory."""
    directory = skills_dir or get_skills_dir()
    if not directory.exists():
        return []

    skills: list[dict] = []
    for path in sorted(directory.glob("*.md")):
        try:
            content = path.read_text(encoding="utf-8")
            skills.append({
                "name": path.stem,
                "path": str(path),
                "content": content,
            })
        except OSError as e:
            logger.warning("Failed to load skill %s: %s", path, e)

    return skills
