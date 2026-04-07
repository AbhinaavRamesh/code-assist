"""Diff tracking per tool use."""

from __future__ import annotations

import difflib
from dataclasses import dataclass


@dataclass
class FileDiff:
    """Diff for a single file."""

    filename: str = ""
    status: str = "modified"  # modified, added, deleted
    additions: int = 0
    deletions: int = 0
    patch: str = ""


def compute_diff(
    old_content: str,
    new_content: str,
    filename: str = "",
) -> FileDiff:
    """Compute a unified diff between old and new content."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff_lines = list(
        difflib.unified_diff(old_lines, new_lines, fromfile=filename, tofile=filename)
    )

    additions = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
    deletions = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))

    status = "modified"
    if not old_content:
        status = "added"
    elif not new_content:
        status = "deleted"

    return FileDiff(
        filename=filename,
        status=status,
        additions=additions,
        deletions=deletions,
        patch="".join(diff_lines),
    )
