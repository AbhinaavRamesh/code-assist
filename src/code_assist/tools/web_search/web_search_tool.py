"""WebSearch tool - web search placeholder.

Currently returns a placeholder message. A real backend (API key, search
provider) is required for actual web search functionality.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from code_assist.tools.base import (
    CanUseToolFn,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
)
from code_assist.types.message import AssistantMessage


# ---------------------------------------------------------------------------
# Input Schema
# ---------------------------------------------------------------------------


class WebSearchInput(BaseModel):
    """Input for the WebSearch tool."""

    query: str = Field(description="Search query")


# ---------------------------------------------------------------------------
# Tool Implementation
# ---------------------------------------------------------------------------


class WebSearchTool(ToolDef):
    """Web search tool (placeholder).

    Returns a message indicating that web search is not yet configured.
    A real implementation would integrate with a search API provider.
    """

    name = "WebSearch"
    search_hint = "web search query internet"
    max_result_size_chars = 50_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return WebSearchInput

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        return ToolResult(data="Web search not yet configured")

    async def description(self, input: BaseModel, options: Any) -> str:
        args: WebSearchInput = input  # type: ignore[assignment]
        return f"WebSearch: {args.query}"

    def is_read_only(self, input: BaseModel) -> bool:
        return True

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True
