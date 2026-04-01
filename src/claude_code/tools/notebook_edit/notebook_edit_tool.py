"""NotebookEdit tool implementation.

Edits cells in Jupyter ``.ipynb`` notebook files.
"""

from __future__ import annotations

import json
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


class NotebookEditInput(BaseModel):
    """Input schema for the NotebookEdit tool."""

    notebook_path: str = Field(description="The absolute path to the .ipynb file")
    cell_number: int = Field(description="0-based index of the cell to edit")
    new_source: str = Field(description="New source content for the cell")
    cell_type: str = Field(
        default="code",
        description="Cell type: 'code' or 'markdown'",
    )


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------


class NotebookEditTool(ToolDef):
    """Edit a cell in a Jupyter notebook."""

    name = "NotebookEdit"
    aliases = ["notebook_edit"]
    max_result_size_chars = 10_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return NotebookEditInput

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        inp: NotebookEditInput = args  # type: ignore[assignment]
        cwd = _get_cwd(context)
        path = expand_path(inp.notebook_path, cwd)

        if not os.path.isfile(path):
            return ToolResult(data=f"Notebook not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                notebook = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            return ToolResult(data=f"Error reading notebook: {exc}")

        cells = notebook.get("cells", [])
        if inp.cell_number < 0 or inp.cell_number >= len(cells):
            return ToolResult(
                data=(
                    f"Cell index {inp.cell_number} out of range. "
                    f"Notebook has {len(cells)} cell(s) (0-indexed)."
                )
            )

        cell = cells[inp.cell_number]

        # Split source into lines for notebook format (list of strings)
        source_lines = _to_notebook_lines(inp.new_source)
        cell["source"] = source_lines
        cell["cell_type"] = inp.cell_type

        # Clear outputs when changing a code cell
        if inp.cell_type == "code":
            cell.setdefault("outputs", [])
            cell["outputs"] = []
            cell.setdefault("execution_count", None)
            cell["execution_count"] = None

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(notebook, f, indent=1, ensure_ascii=False)
                f.write("\n")
        except OSError as exc:
            return ToolResult(data=f"Error writing notebook: {exc}")

        return ToolResult(
            data=(
                f"Updated cell {inp.cell_number} in {path} "
                f"(type={inp.cell_type}, {len(source_lines)} line(s))"
            )
        )

    async def description(
        self,
        input: BaseModel,
        options: DescriptionOptions,
    ) -> str:
        inp: NotebookEditInput = input  # type: ignore[assignment]
        return f"Edit cell {inp.cell_number} in {inp.notebook_path}"

    def is_read_only(self, input: BaseModel) -> bool:
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return False


def _to_notebook_lines(source: str) -> list[str]:
    """Convert a string into the notebook source format (list of lines with \\n)."""
    if not source:
        return []
    lines = source.split("\n")
    # Each line except the last gets a trailing newline
    result: list[str] = []
    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            result.append(line + "\n")
        else:
            # Last line: include it only if non-empty (no trailing newline)
            if line:
                result.append(line)
    return result


def _get_cwd(context: ToolUseContext) -> str:
    import os

    state = context.get_app_state()
    if state and hasattr(state, "cwd"):
        return str(state.cwd)
    return os.getcwd()
