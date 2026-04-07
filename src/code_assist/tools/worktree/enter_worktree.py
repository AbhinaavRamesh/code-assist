"""EnterWorktree tool - creates and enters a git worktree for isolated work.

Creates an isolated git worktree so the agent can work on a separate copy
of the repo without affecting the main working tree. Useful for parallel
branches, experiments, or agent isolation.
"""

from __future__ import annotations

import logging
import os
import re
import uuid
from typing import Any

from pydantic import BaseModel, Field

from code_assist.git.operations import get_git_root, is_git_repo
from code_assist.git.worktree import WorktreeInfo, create_worktree
from code_assist.tools.base import (
    CanUseToolFn,
    DescriptionOptions,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
    ValidationResult,
)
from code_assist.types.message import AssistantMessage

logger = logging.getLogger(__name__)

_SLUG_PATTERN = re.compile(r"^[a-zA-Z0-9._/-]{1,64}$")


class EnterWorktreeInput(BaseModel):
    """Input schema for EnterWorktree."""

    name: str | None = Field(
        default=None,
        description=(
            "Optional name for the worktree. Each segment may contain only "
            "letters, digits, dots, underscores, and dashes; max 64 chars. "
            "A random name is generated if not provided."
        ),
    )


class EnterWorktreeTool(ToolDef):
    """Create an isolated git worktree and switch the session into it.

    The worktree is created as a sibling of the main repo directory.
    Use ExitWorktree to leave and optionally clean up.
    """

    name = "EnterWorktree"
    search_hint = "create an isolated git worktree and switch into it"
    max_result_size_chars = 100_000
    should_defer = True

    @property
    def input_schema(self) -> type[BaseModel]:
        return EnterWorktreeInput

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        inp: EnterWorktreeInput = input  # type: ignore[assignment]
        if inp.name and not _SLUG_PATTERN.match(inp.name):
            return ValidationResult(
                result=False,
                message=(
                    f"Invalid worktree name: '{inp.name}'. "
                    "Use only letters, digits, dots, underscores, dashes (max 64 chars)."
                ),
                error_code=1,
            )
        return ValidationResult(result=True)

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        inp: EnterWorktreeInput = args  # type: ignore[assignment]

        # Check if already in a worktree session
        state = context.get_app_state()
        if isinstance(state, dict) and state.get("worktreeSession"):
            return ToolResult(
                data={"error": "Already in a worktree session. Use ExitWorktree first."}
            )

        # Find the git root
        cwd = os.getcwd()
        if not await is_git_repo(cwd):
            return ToolResult(
                data={"error": "Not in a git repository. Worktrees require git."}
            )

        git_root = await get_git_root(cwd)
        if not git_root:
            return ToolResult(
                data={"error": "Could not determine git root directory."}
            )

        # Generate worktree slug and path
        slug = inp.name or f"wt-{uuid.uuid4().hex[:8]}"
        branch_name = f"worktree/{slug}"
        worktree_path = os.path.join(
            os.path.dirname(git_root), f".worktrees/{slug}"
        )

        # Create the worktree
        result = await create_worktree(
            worktree_path, branch_name, cwd=git_root, new_branch=True
        )

        if not result.success:
            return ToolResult(
                data={
                    "error": f"Failed to create worktree: {result.error}",
                    "git_output": result.output,
                }
            )

        # Update AppState with worktree session info
        session_info: dict[str, Any] = {
            "worktreePath": worktree_path,
            "worktreeBranch": branch_name,
            "originalCwd": cwd,
            "slug": slug,
        }

        def _enter(prev: Any) -> Any:
            if isinstance(prev, dict):
                return {**prev, "worktreeSession": session_info}
            return prev

        context.set_app_state(_enter)

        # Change the working directory
        try:
            os.chdir(worktree_path)
        except OSError as exc:
            logger.warning("Failed to chdir to worktree: %s", exc)

        branch_info = f" on branch {branch_name}" if branch_name else ""
        return ToolResult(
            data={
                "worktreePath": worktree_path,
                "worktreeBranch": branch_name,
                "message": (
                    f"Created worktree at {worktree_path}{branch_info}. "
                    "The session is now working in the worktree. "
                    "Use ExitWorktree to leave mid-session."
                ),
            }
        )

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        return "Creates an isolated worktree and switches the session into it"

    def is_read_only(self, input: BaseModel) -> bool:
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return False
