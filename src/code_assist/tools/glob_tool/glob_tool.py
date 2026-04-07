"""Glob tool - fast file pattern matching.

Searches for files matching glob patterns, sorted by modification time.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from code_assist.tools.base import (
    CanUseToolFn,
    SearchOrReadInfo,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
)
from code_assist.types.message import AssistantMessage


# ---------------------------------------------------------------------------
# Input Schema
# ---------------------------------------------------------------------------

MAX_RESULTS = 1000


class GlobInput(BaseModel):
    """Input for the Glob tool."""

    pattern: str = Field(description="Glob pattern to match files (e.g. '**/*.py')")
    path: str | None = Field(
        default=None,
        description="Directory to search in. Defaults to current working directory.",
    )


# ---------------------------------------------------------------------------
# Tool Implementation
# ---------------------------------------------------------------------------


class GlobTool(ToolDef):
    """Fast file pattern matching tool.

    Searches for files matching glob patterns and returns matching file paths
    sorted by modification time (most recently modified first).
    """

    name = "Glob"
    search_hint = "find files by pattern glob search"
    max_result_size_chars = 100_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return GlobInput

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        input_args: GlobInput = args  # type: ignore[assignment]

        search_dir = Path(input_args.path) if input_args.path else Path.cwd()
        if not search_dir.is_dir():
            return ToolResult(data=f"Error: directory '{search_dir}' does not exist")

        pattern = input_args.pattern

        try:
            matches = list(search_dir.glob(pattern))
        except Exception as exc:
            return ToolResult(data=f"Error matching pattern '{pattern}': {exc}")

        # Filter to files only (exclude directories)
        file_matches = [p for p in matches if p.is_file()]

        # Sort by modification time (most recent first)
        file_matches.sort(key=lambda p: _safe_mtime(p), reverse=True)

        # Limit results
        truncated = len(file_matches) > MAX_RESULTS
        file_matches = file_matches[:MAX_RESULTS]

        # Format output
        lines = [str(p) for p in file_matches]
        if truncated:
            lines.append(f"\n(Results truncated to {MAX_RESULTS} files)")

        return ToolResult(data="\n".join(lines) if lines else "No files matched.")

    async def description(self, input: BaseModel, options: Any) -> str:
        args: GlobInput = input  # type: ignore[assignment]
        return f"Glob: {args.pattern}"

    def is_read_only(self, input: BaseModel) -> bool:
        return True

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True

    def is_search_or_read_command(self, input: BaseModel) -> SearchOrReadInfo:
        return SearchOrReadInfo(is_search=True)


def _safe_mtime(path: Path) -> float:
    """Get modification time, returning 0 on error."""
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0
