"""FileRead tool implementation.

Reads files from the filesystem with line numbers, offset/limit support,
and binary detection.
"""

from __future__ import annotations

import math
from typing import Any

from pydantic import BaseModel, Field

from claude_code.tools.base import (
    CanUseToolFn,
    DescriptionOptions,
    SearchOrReadInfo,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
)
from claude_code.types.message import AssistantMessage
from claude_code.utils.file import expand_path, is_binary_file, suggest_similar_files
from claude_code.utils.file_read import read_file_with_line_numbers


# ---------------------------------------------------------------------------
# Input Schema
# ---------------------------------------------------------------------------


class FileReadInput(BaseModel):
    """Input schema for the FileRead tool."""

    file_path: str = Field(description="The absolute path to the file to read")
    offset: int | None = Field(
        default=None,
        description="Line offset to start reading from (0-based)",
    )
    limit: int | None = Field(
        default=None,
        description="Maximum number of lines to read",
    )
    pages: str | None = Field(
        default=None,
        description="Page range for PDF files (e.g. '1-5')",
    )


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

_DEFAULT_LIMIT = 2000


class FileReadTool(ToolDef):
    """Read a file from disk with line numbers."""

    name = "Read"
    aliases = ["file_read", "read"]
    max_result_size_chars = math.inf  # type: ignore[assignment]

    @property
    def input_schema(self) -> type[BaseModel]:
        return FileReadInput

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        inp: FileReadInput = args  # type: ignore[assignment]
        cwd = _get_cwd(context)
        path = expand_path(inp.file_path, cwd)

        import os

        if not os.path.exists(path):
            suggestions = suggest_similar_files(path, cwd)
            msg = f"File not found: {path}"
            if suggestions:
                msg += "\n\nDid you mean one of these?\n" + "\n".join(
                    f"  - {s}" for s in suggestions
                )
            return ToolResult(data=msg)

        if not os.path.isfile(path):
            return ToolResult(data=f"Not a regular file: {path}")

        if is_binary_file(path):
            size = os.path.getsize(path)
            return ToolResult(data=f"Binary file ({size} bytes): {path}")

        offset = inp.offset or 0
        limit = inp.limit or _DEFAULT_LIMIT

        try:
            content = read_file_with_line_numbers(path, offset=offset, limit=limit)
        except OSError as exc:
            return ToolResult(data=f"Error reading file: {exc}")

        return ToolResult(data=content)

    async def description(
        self,
        input: BaseModel,
        options: DescriptionOptions,
    ) -> str:
        inp: FileReadInput = input  # type: ignore[assignment]
        return f"Read {inp.file_path}"

    def is_read_only(self, input: BaseModel) -> bool:
        return True

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True

    def is_search_or_read_command(self, input: BaseModel) -> SearchOrReadInfo:
        return SearchOrReadInfo(is_read=True)


def _get_cwd(context: ToolUseContext) -> str:
    """Extract the current working directory from context or fall back to os.getcwd."""
    import os

    state = context.get_app_state()
    if state and hasattr(state, "cwd"):
        return str(state.cwd)
    return os.getcwd()
