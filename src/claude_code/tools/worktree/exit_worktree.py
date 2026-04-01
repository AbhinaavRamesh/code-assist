"""ExitWorktree tool - exits the current git worktree and returns to the main tree.

Supports two actions:
  - 'keep': leaves the worktree and branch on disk
  - 'remove': deletes the worktree and branch (requires discard_changes=True
    if there are uncommitted changes or unmerged commits)
"""

from __future__ import annotations

import logging
import os
from typing import Any, Literal

from pydantic import BaseModel, Field

from claude_code.git.operations import run_git
from claude_code.git.worktree import remove_worktree
from claude_code.tools.base import (
    CanUseToolFn,
    DescriptionOptions,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
    ValidationResult,
)
from claude_code.types.message import AssistantMessage

logger = logging.getLogger(__name__)


class ExitWorktreeInput(BaseModel):
    """Input schema for ExitWorktree."""

    action: Literal["keep", "remove"] = Field(
        ...,
        description='"keep" leaves the worktree on disk; "remove" deletes it.',
    )
    discard_changes: bool | None = Field(
        default=None,
        description=(
            "Required true when action is 'remove' and the worktree has "
            "uncommitted files or unmerged commits."
        ),
    )


async def _count_worktree_changes(worktree_path: str) -> dict[str, int] | None:
    """Count changed files and unmerged commits in a worktree."""
    status = await run_git("-C", worktree_path, "status", "--porcelain")
    if not status.success:
        return None

    changed_files = sum(
        1 for line in status.output.splitlines() if line.strip()
    )
    return {"changed_files": changed_files}


class ExitWorktreeTool(ToolDef):
    """Exit the current git worktree and return to the original directory.

    If action is 'remove', the worktree directory and its branch are deleted.
    If the worktree has uncommitted changes, discard_changes must be True.
    """

    name = "ExitWorktree"
    search_hint = "exit a worktree session and return to the original directory"
    max_result_size_chars = 100_000
    should_defer = True

    @property
    def input_schema(self) -> type[BaseModel]:
        return ExitWorktreeInput

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        inp: ExitWorktreeInput = input  # type: ignore[assignment]

        # Verify we are in a worktree session
        state = context.get_app_state()
        session = None
        if isinstance(state, dict):
            session = state.get("worktreeSession")
        if session is None:
            return ValidationResult(
                result=False,
                message="Not in a worktree session.",
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
        inp: ExitWorktreeInput = args  # type: ignore[assignment]

        state = context.get_app_state()
        session: dict[str, Any] | None = None
        if isinstance(state, dict):
            session = state.get("worktreeSession")

        if session is None:
            return ToolResult(
                data={"error": "Not in a worktree session."}
            )

        worktree_path = session.get("worktreePath", "")
        worktree_branch = session.get("worktreeBranch")
        original_cwd = session.get("originalCwd", os.path.expanduser("~"))

        output: dict[str, Any] = {
            "action": inp.action,
            "originalCwd": original_cwd,
            "worktreePath": worktree_path,
            "worktreeBranch": worktree_branch,
        }

        if inp.action == "remove":
            # Check for uncommitted changes
            if worktree_path and os.path.isdir(worktree_path):
                changes = await _count_worktree_changes(worktree_path)
                if changes and changes["changed_files"] > 0:
                    if not inp.discard_changes:
                        return ToolResult(
                            data={
                                "error": (
                                    f"Worktree has {changes['changed_files']} uncommitted file(s). "
                                    "Set discard_changes=true to force removal, or use action='keep'."
                                ),
                                "changed_files": changes["changed_files"],
                            }
                        )
                    output["discardedFiles"] = changes["changed_files"]

                # Remove the worktree
                result = await remove_worktree(
                    worktree_path, force=bool(inp.discard_changes), cwd=original_cwd
                )
                if not result.success:
                    return ToolResult(
                        data={
                            "error": f"Failed to remove worktree: {result.error}",
                            "worktreePath": worktree_path,
                        }
                    )
        # 'keep' action: just leave the worktree on disk

        # Return to original directory
        try:
            os.chdir(original_cwd)
        except OSError as exc:
            logger.warning("Failed to chdir back to %s: %s", original_cwd, exc)

        # Clear worktree session from AppState
        def _clear(prev: Any) -> Any:
            if isinstance(prev, dict):
                new = {**prev}
                new.pop("worktreeSession", None)
                return new
            return prev

        context.set_app_state(_clear)

        verb = "removed" if inp.action == "remove" else "kept"
        output["message"] = (
            f"Exited worktree. Worktree at {worktree_path} was {verb}. "
            f"Returned to {original_cwd}."
        )

        return ToolResult(data=output)

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        inp: ExitWorktreeInput = input  # type: ignore[assignment]
        return f"Exiting worktree ({inp.action})"

    def is_read_only(self, input: BaseModel) -> bool:
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return False
