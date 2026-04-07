"""ToolSearch tool - search available tools by name and description.

Searches through the available tools by matching against tool names,
aliases, and search hints. Returns matching tool schemas.
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


class ToolSearchInput(BaseModel):
    """Input for the ToolSearch tool."""

    query: str = Field(description="Query to search for tools")
    max_results: int = Field(default=5, description="Maximum number of results")


# ---------------------------------------------------------------------------
# Tool Implementation
# ---------------------------------------------------------------------------


class ToolSearchTool(ToolDef):
    """Search through available tools by name and description.

    Matches the query against tool names, aliases, and search_hint fields,
    then returns matching tool schemas.
    """

    name = "ToolSearch"
    search_hint = "find tool search discover available"
    max_result_size_chars = 50_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return ToolSearchInput

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        input_args: ToolSearchInput = args  # type: ignore[assignment]
        query = input_args.query.lower()
        max_results = input_args.max_results

        available_tools = context.tools

        scored: list[tuple[float, Any]] = []
        for tool in available_tools:
            score = _score_tool(tool, query)
            if score > 0:
                scored.append((score, tool))

        # Sort by score descending
        scored.sort(key=lambda item: item[0], reverse=True)
        scored = scored[:max_results]

        if not scored:
            return ToolResult(data=f"No tools matched query: {input_args.query}")

        lines: list[str] = []
        for _score, tool in scored:
            name = getattr(tool, "name", "unknown")
            aliases = getattr(tool, "aliases", [])
            hint = getattr(tool, "search_hint", "") or ""

            schema_info = ""
            schema_cls = getattr(tool, "input_schema", None)
            if schema_cls and hasattr(schema_cls, "model_json_schema"):
                try:
                    schema_info = str(schema_cls.model_json_schema())
                except Exception:
                    pass

            entry = f"- {name}"
            if aliases:
                entry += f" (aliases: {', '.join(aliases)})"
            if hint:
                entry += f"\n  Hint: {hint}"
            if schema_info:
                entry += f"\n  Schema: {schema_info}"
            lines.append(entry)

        return ToolResult(data="\n".join(lines))

    async def description(self, input: BaseModel, options: Any) -> str:
        args: ToolSearchInput = input  # type: ignore[assignment]
        return f"ToolSearch: {args.query}"

    def is_read_only(self, input: BaseModel) -> bool:
        return True

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def _score_tool(tool: Any, query: str) -> float:
    """Score how well a tool matches the query. Returns 0 for no match."""
    score = 0.0
    name = getattr(tool, "name", "").lower()
    aliases = [a.lower() for a in getattr(tool, "aliases", [])]
    hint = (getattr(tool, "search_hint", "") or "").lower()

    query_terms = query.split()

    # Exact name match
    if query == name:
        score += 10.0
    # Exact alias match
    elif query in aliases:
        score += 8.0
    # Partial name match
    elif query in name:
        score += 5.0
    # Name contains a query term
    elif any(term in name for term in query_terms):
        score += 3.0

    # Search hint matching
    for term in query_terms:
        if term in hint:
            score += 2.0

    # Alias partial matching
    for alias in aliases:
        if query in alias:
            score += 1.0

    return score
