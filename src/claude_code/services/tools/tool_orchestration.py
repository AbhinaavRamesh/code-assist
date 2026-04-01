"""Tool orchestration - concurrent/sequential tool execution.

Tool orchestration for concurrent/sequential execution.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from claude_code.services.tools.tool_execution import (
    ToolExecutionResult,
    execute_tool_use,
)
from claude_code.tools.base import CanUseToolFn, ToolCallProgress, ToolUseContext
from claude_code.types.message import AssistantMessage

logger = logging.getLogger(__name__)


async def execute_tool_uses(
    tool_uses: list[dict[str, Any]],
    *,
    context: ToolUseContext,
    can_use_tool: CanUseToolFn,
    parent_message: AssistantMessage,
    on_progress: ToolCallProgress | None = None,
) -> list[ToolExecutionResult]:
    """Execute multiple tool use blocks, respecting concurrency safety.

    Tools that are concurrency-safe run in parallel.
    Non-concurrency-safe tools run sequentially.
    """
    if not tool_uses:
        return []

    # Partition into concurrent and sequential groups
    concurrent: list[dict[str, Any]] = []
    sequential: list[dict[str, Any]] = []

    for tu in tool_uses:
        tool_name = tu.get("name", "")
        tool = None
        for t in context.tools:
            if t.name == tool_name:
                tool = t
                break

        # Default to sequential if we can't determine concurrency safety
        if tool is not None:
            try:
                from pydantic import BaseModel

                parsed = tool.input_schema.model_validate(tu.get("input", {}))
                if tool.is_concurrency_safe(parsed):
                    concurrent.append(tu)
                else:
                    sequential.append(tu)
            except Exception:
                sequential.append(tu)
        else:
            sequential.append(tu)

    results: list[ToolExecutionResult] = []

    # Run concurrent tools in parallel
    if concurrent:
        tasks = [
            execute_tool_use(
                tu["id"],
                tu["name"],
                tu.get("input", {}),
                context=context,
                can_use_tool=can_use_tool,
                parent_message=parent_message,
                on_progress=on_progress,
            )
            for tu in concurrent
        ]
        concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in concurrent_results:
            if isinstance(r, Exception):
                results.append(
                    ToolExecutionResult(
                        tool_use_id="unknown",
                        tool_name="unknown",
                        error=str(r),
                    )
                )
            else:
                results.append(r)

    # Run sequential tools one at a time
    for tu in sequential:
        result = await execute_tool_use(
            tu["id"],
            tu["name"],
            tu.get("input", {}),
            context=context,
            can_use_tool=can_use_tool,
            parent_message=parent_message,
            on_progress=on_progress,
        )
        results.append(result)

    return results
