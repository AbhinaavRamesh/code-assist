"""FileWrite tool implementation.

Writes content to a file, creating parent directories as needed.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field

from claude_code.tools.base import (
    CanUseToolFn,
    DescriptionOptions,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
)
from claude_code.types.message import AssistantMessage
from claude_code.utils.file import expand_path


# ---------------------------------------------------------------------------
# Input Schema
# ---------------------------------------------------------------------------


class FileWriteInput(BaseModel):
    """Input schema for the FileWrite tool."""

    file_path: str = Field(description="The absolute path to the file to write")
    content: str = Field(description="The content to write to the file")


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------


class FileWriteTool(ToolDef):
    """Write content to a file on disk."""

    name = "Write"
    aliases = ["file_write", "write"]
    max_result_size_chars = 10_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return FileWriteInput

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        inp: FileWriteInput = args  # type: ignore[assignment]
        cwd = _get_cwd(context)
        path = expand_path(inp.file_path, cwd)

        existed = os.path.exists(path)

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(inp.content)
        except OSError as exc:
            return ToolResult(data=f"Error writing file: {exc}")

        action = "Updated" if existed else "Created"
        size = os.path.getsize(path)
        return ToolResult(data=f"{action} file: {path} ({size} bytes)")

    async def description(
        self,
        input: BaseModel,
        options: DescriptionOptions,
    ) -> str:
        inp: FileWriteInput = input  # type: ignore[assignment]
        return f"Write {inp.file_path}"

    def is_read_only(self, input: BaseModel) -> bool:
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return False


def _get_cwd(context: ToolUseContext) -> str:
    import os

    state = context.get_app_state()
    if state and hasattr(state, "cwd"):
        return str(state.cwd)
    return os.getcwd()
