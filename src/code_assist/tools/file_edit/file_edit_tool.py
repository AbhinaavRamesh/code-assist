"""FileEdit tool implementation.

Performs exact string replacements in files with uniqueness validation.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field

from code_assist.tools.base import (
    CanUseToolFn,
    DescriptionOptions,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
)
from code_assist.types.message import AssistantMessage
from code_assist.utils.file import expand_path


# ---------------------------------------------------------------------------
# Input Schema
# ---------------------------------------------------------------------------


class FileEditInput(BaseModel):
    """Input schema for the FileEdit tool."""

    file_path: str = Field(description="The absolute path to the file to edit")
    old_string: str = Field(description="The text to replace")
    new_string: str = Field(description="The replacement text")
    replace_all: bool = Field(
        default=False,
        description="Replace all occurrences instead of requiring uniqueness",
    )


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------


class FileEditTool(ToolDef):
    """Perform exact string replacement in a file."""

    name = "Edit"
    aliases = ["file_edit", "edit"]
    max_result_size_chars = 10_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return FileEditInput

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        inp: FileEditInput = args  # type: ignore[assignment]
        cwd = _get_cwd(context)
        path = expand_path(inp.file_path, cwd)

        if not os.path.isfile(path):
            return ToolResult(data=f"File not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as exc:
            return ToolResult(data=f"Error reading file: {exc}")

        if inp.old_string == inp.new_string:
            return ToolResult(data="old_string and new_string are identical; no changes made.")

        occurrences = content.count(inp.old_string)

        if occurrences == 0:
            return ToolResult(
                data=f"old_string not found in {path}. No changes made."
            )

        if occurrences > 1 and not inp.replace_all:
            return ToolResult(
                data=(
                    f"old_string appears {occurrences} times in {path}. "
                    "Provide a larger unique string or set replace_all=True."
                )
            )

        new_content = content.replace(inp.old_string, inp.new_string)
        if inp.replace_all:
            replaced_count = occurrences
        else:
            new_content = content.replace(inp.old_string, inp.new_string, 1)
            replaced_count = 1

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
        except OSError as exc:
            return ToolResult(data=f"Error writing file: {exc}")

        # Build a simple diff summary
        return ToolResult(
            data=(
                f"Replaced {replaced_count} occurrence(s) in {path}.\n"
                f"  - old ({len(inp.old_string)} chars): "
                f"{_preview(inp.old_string)}\n"
                f"  + new ({len(inp.new_string)} chars): "
                f"{_preview(inp.new_string)}"
            )
        )

    async def description(
        self,
        input: BaseModel,
        options: DescriptionOptions,
    ) -> str:
        inp: FileEditInput = input  # type: ignore[assignment]
        return f"Edit {inp.file_path}"

    def is_read_only(self, input: BaseModel) -> bool:
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return False


def _preview(text: str, max_len: int = 80) -> str:
    """Return a truncated single-line preview of *text*."""
    line = text.replace("\n", "\\n")
    if len(line) > max_len:
        return line[: max_len - 3] + "..."
    return line


def _get_cwd(context: ToolUseContext) -> str:
    import os

    state = context.get_app_state()
    if state and hasattr(state, "cwd"):
        return str(state.cwd)
    return os.getcwd()
