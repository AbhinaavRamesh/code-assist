"""Single tool execution with permission checking.

Ports the TypeScript tool execution from src/services/tools/.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from code_assist.tools.base import (
    CanUseToolFn,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
    find_tool_by_name,
)
from code_assist.types.message import AssistantMessage

logger = logging.getLogger(__name__)


@dataclass
class ToolExecutionResult:
    """Result of executing a tool use block."""

    tool_use_id: str
    tool_name: str
    result: ToolResult | None = None
    error: str | None = None
    duration_ms: float = 0
    was_denied: bool = False


async def execute_tool_use(
    tool_use_id: str,
    tool_name: str,
    tool_input: dict[str, Any],
    *,
    context: ToolUseContext,
    can_use_tool: CanUseToolFn,
    parent_message: AssistantMessage,
    on_progress: ToolCallProgress | None = None,
) -> ToolExecutionResult:
    """Execute a single tool use block.

    1. Find the tool by name
    2. Parse and validate input
    3. Check permissions
    4. Execute the tool
    5. Return result
    """
    start = time.monotonic()

    # Find the tool
    tool = find_tool_by_name(context.tools, tool_name)
    if tool is None:
        return ToolExecutionResult(
            tool_use_id=tool_use_id,
            tool_name=tool_name,
            error=f"Unknown tool: {tool_name}",
        )

    # Check if enabled
    if not tool.is_enabled():
        return ToolExecutionResult(
            tool_use_id=tool_use_id,
            tool_name=tool_name,
            error=f"Tool {tool_name} is not currently enabled.",
        )

    # Parse input
    try:
        parsed_input = tool.input_schema.model_validate(tool_input)
    except (ValidationError, Exception) as e:
        return ToolExecutionResult(
            tool_use_id=tool_use_id,
            tool_name=tool_name,
            error=f"Invalid input for {tool_name}: {e}",
        )

    # Validate input
    validation = await tool.validate_input(parsed_input, context)
    if not validation.result:
        return ToolExecutionResult(
            tool_use_id=tool_use_id,
            tool_name=tool_name,
            error=validation.message,
        )

    # Execute
    try:
        result = await tool.call(
            parsed_input,
            context,
            can_use_tool,
            parent_message,
            on_progress,
        )
        duration = (time.monotonic() - start) * 1000
        return ToolExecutionResult(
            tool_use_id=tool_use_id,
            tool_name=tool_name,
            result=result,
            duration_ms=duration,
        )
    except Exception as e:
        duration = (time.monotonic() - start) * 1000
        logger.error("Tool %s failed: %s", tool_name, e, exc_info=True)
        return ToolExecutionResult(
            tool_use_id=tool_use_id,
            tool_name=tool_name,
            error=str(e),
            duration_ms=duration,
        )
