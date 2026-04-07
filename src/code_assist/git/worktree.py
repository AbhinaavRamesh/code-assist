"""Git worktree management."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from code_assist.git.operations import GitResult, run_git

logger = logging.getLogger(__name__)


@dataclass
class WorktreeInfo:
    """Information about a git worktree."""

    path: str = ""
    branch: str = ""
    original_commit: str = ""
    is_active: bool = True


async def create_worktree(
    path: str,
    branch: str | None = None,
    *,
    cwd: str | None = None,
    new_branch: bool = True,
) -> GitResult:
    """Create a git worktree."""
    args = ["worktree", "add"]
    if new_branch and branch:
        args.extend(["-b", branch])
    args.append(path)
    if branch and not new_branch:
        args.append(branch)
    return await run_git(*args, cwd=cwd)


async def remove_worktree(
    path: str,
    *,
    force: bool = False,
    cwd: str | None = None,
) -> GitResult:
    """Remove a git worktree."""
    args = ["worktree", "remove"]
    if force:
        args.append("--force")
    args.append(path)
    return await run_git(*args, cwd=cwd)


async def list_worktrees(cwd: str | None = None) -> list[WorktreeInfo]:
    """List all git worktrees."""
    result = await run_git("worktree", "list", "--porcelain", cwd=cwd)
    if not result.success:
        return []

    worktrees: list[WorktreeInfo] = []
    current: dict[str, str] = {}
    for line in result.output.splitlines():
        if not line.strip():
            if current:
                worktrees.append(
                    WorktreeInfo(
                        path=current.get("worktree", ""),
                        branch=current.get("branch", "").replace("refs/heads/", ""),
                    )
                )
                current = {}
        elif line.startswith("worktree "):
            current["worktree"] = line[9:]
        elif line.startswith("branch "):
            current["branch"] = line[7:]

    if current:
        worktrees.append(
            WorktreeInfo(
                path=current.get("worktree", ""),
                branch=current.get("branch", "").replace("refs/heads/", ""),
            )
        )

    return worktrees
