"""LSPTool - interacts with a Language Server Protocol server."""

from __future__ import annotations

from typing import Any

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


class LSPToolInput(BaseModel):
    """Input schema for LSPTool."""

    operation: str = Field(
        ...,
        description="LSP operation to perform (e.g. hover, definition, references, diagnostics)",
    )
    file_path: str = Field(..., description="Path to the file to operate on")
    position: dict[str, Any] | None = Field(
        default=None,
        description="Cursor position as {line: int, character: int}",
    )


class LSPTool(ToolDef):
    """Interact with a Language Server Protocol server for code intelligence."""

    name = "LSP"
    max_result_size_chars = 100_000
    is_lsp = True

    @property
    def input_schema(self) -> type[BaseModel]:
        return LSPToolInput

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        inp: LSPToolInput = args  # type: ignore[assignment]
        # Placeholder: real implementation would connect to the LSP server
        # and perform the requested operation.
        pos_str = ""
        if inp.position:
            pos_str = f" at line {inp.position.get('line', '?')}"
        return ToolResult(
            data=f"LSP {inp.operation} on {inp.file_path}{pos_str}: (no results)"
        )

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        inp: LSPToolInput = input  # type: ignore[assignment]
        return f"LSP {inp.operation}: {inp.file_path}"

    def is_read_only(self, input: BaseModel) -> bool:
        return True

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True
