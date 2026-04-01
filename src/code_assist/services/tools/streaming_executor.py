"""Streaming tool executor - parallel tool execution during streaming.

Streaming tool executor for parallel execution during streaming.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from code_assist.services.tools.tool_execution import (
    ToolExecutionResult,
    execute_tool_use,
)
from code_assist.tools.base import CanUseToolFn, ToolCallProgress, ToolUseContext
from code_assist.types.message import AssistantMessage

logger = logging.getLogger(__name__)


class StreamingToolExecutor:
    """Executes tools as they arrive during streaming.

    Starts execution as soon as a complete tool_use block is received,
    without waiting for the full assistant message to complete.
    """

    def __init__(
        self,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> None:
        self._context = context
        self._can_use_tool = can_use_tool
        self._parent_message = parent_message
        self._on_progress = on_progress
        self._pending: dict[str, asyncio.Task[ToolExecutionResult]] = {}
        self._results: dict[str, ToolExecutionResult] = {}

    def submit(
        self,
        tool_use_id: str,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> None:
        """Submit a tool use for execution."""
        if tool_use_id in self._pending or tool_use_id in self._results:
            return

        task = asyncio.create_task(
            execute_tool_use(
                tool_use_id,
                tool_name,
                tool_input,
                context=self._context,
                can_use_tool=self._can_use_tool,
                parent_message=self._parent_message,
                on_progress=self._on_progress,
            )
        )
        self._pending[tool_use_id] = task

    async def wait_all(self) -> list[ToolExecutionResult]:
        """Wait for all submitted tools to complete."""
        if self._pending:
            done = await asyncio.gather(
                *self._pending.values(), return_exceptions=True
            )
            for tool_use_id, result in zip(self._pending.keys(), done):
                if isinstance(result, Exception):
                    self._results[tool_use_id] = ToolExecutionResult(
                        tool_use_id=tool_use_id,
                        tool_name="unknown",
                        error=str(result),
                    )
                else:
                    self._results[tool_use_id] = result
            self._pending.clear()

        return list(self._results.values())

    async def wait_one(self, tool_use_id: str) -> ToolExecutionResult | None:
        """Wait for a specific tool to complete."""
        if tool_use_id in self._results:
            return self._results[tool_use_id]
        task = self._pending.get(tool_use_id)
        if task is None:
            return None
        try:
            result = await task
            self._results[tool_use_id] = result
            del self._pending[tool_use_id]
            return result
        except Exception as e:
            result = ToolExecutionResult(
                tool_use_id=tool_use_id,
                tool_name="unknown",
                error=str(e),
            )
            self._results[tool_use_id] = result
            del self._pending[tool_use_id]
            return result

    @property
    def has_pending(self) -> bool:
        """Whether there are pending tool executions."""
        return bool(self._pending)
