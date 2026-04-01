"""Git operation wrappers."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GitResult:
    """Result of a git operation."""

    success: bool = True
    output: str = ""
    error: str = ""
    return_code: int = 0


async def run_git(
    *args: str, cwd: str | None = None
) -> GitResult:
    """Run a git command and return the result."""
    cmd = ["git", *args]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        stdout, stderr = await proc.communicate()
        return GitResult(
            success=proc.returncode == 0,
            output=stdout.decode(errors="replace").strip(),
            error=stderr.decode(errors="replace").strip(),
            return_code=proc.returncode or 0,
        )
    except FileNotFoundError:
        return GitResult(success=False, error="git not found", return_code=-1)
    except Exception as e:
        return GitResult(success=False, error=str(e), return_code=-1)


async def git_status(cwd: str | None = None) -> str:
    """Get git status output."""
    result = await run_git("status", "--short", cwd=cwd)
    return result.output


async def git_diff(cwd: str | None = None, staged: bool = False) -> str:
    """Get git diff."""
    args = ["diff"]
    if staged:
        args.append("--staged")
    result = await run_git(*args, cwd=cwd)
    return result.output


async def git_log(
    cwd: str | None = None, n: int = 10, oneline: bool = True
) -> str:
    """Get git log."""
    args = ["log", f"-{n}"]
    if oneline:
        args.append("--oneline")
    result = await run_git(*args, cwd=cwd)
    return result.output


async def git_branch(cwd: str | None = None) -> str:
    """Get current branch name."""
    result = await run_git("branch", "--show-current", cwd=cwd)
    return result.output


async def is_git_repo(cwd: str | None = None) -> bool:
    """Check if the directory is inside a git repo."""
    result = await run_git("rev-parse", "--is-inside-work-tree", cwd=cwd)
    return result.success and result.output == "true"


async def get_git_root(cwd: str | None = None) -> str | None:
    """Get the root of the git repository."""
    result = await run_git("rev-parse", "--show-toplevel", cwd=cwd)
    return result.output if result.success else None
