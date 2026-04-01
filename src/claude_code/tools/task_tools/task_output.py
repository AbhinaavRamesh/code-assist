"""TaskOutput tool - retrieves the output of a task, optionally blocking until complete."""

from __future__ import annotations

import asyncio

from pydantic import BaseModel, Field

from claude_code.tasks.types import Task, TaskStatus
from claude_code.tools.base import (
    CanUseToolFn,
    DescriptionOptions,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
    ValidationResult,
)
from claude_code.types.message import AssistantMessage

_TERMINAL_STATUSES = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.KILLED}
_POLL_INTERVAL_S = 0.1


class TaskOutputInput(BaseModel):
    """Input schema for TaskOutput."""

    task_id: str = Field(..., description="ID of the task to get output for")
    block: bool = Field(
        default=True, description="Whether to wait for task completion"
    )
    timeout: int = Field(
        default=30000,
        description="Max wait time in ms (0-600000)",
        ge=0,
        le=600_000,
    )


class TaskOutputTool(ToolDef):
    """Retrieve the output of a task, optionally waiting for completion."""

    name = "TaskOutput"
    aliases = ["AgentOutputTool", "BashOutputTool"]
    max_result_size_chars = 100_000
    should_defer = True

    @property
    def input_schema(self) -> type[BaseModel]:
        return TaskOutputInput

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        inp: TaskOutputInput = input  # type: ignore[assignment]
        if not inp.task_id.strip():
            return ValidationResult(
                result=False, message="task_id is required", error_code=1
            )
        return ValidationResult(result=True)

    def _get_task_from_state(self, context: ToolUseContext, task_id: str) -> Task | dict | None:  # type: ignore[type-arg]
        """Look up a task in AppState."""
        state = context.get_app_state()
        tasks: dict = {}  # type: ignore[type-arg]
        if isinstance(state, dict):
            tasks = state.get("tasks", {})
        elif state is not None and hasattr(state, "tasks"):
            tasks = getattr(state, "tasks", {})
        return tasks.get(task_id)

    def _get_status(self, task: Task | dict) -> TaskStatus:  # type: ignore[type-arg]
        if isinstance(task, Task):
            return task.status
        if isinstance(task, dict):
            try:
                return TaskStatus(task.get("status", "pending"))
            except ValueError:
                return TaskStatus.PENDING
        return TaskStatus.PENDING

    def _is_terminal(self, task: Task | dict) -> bool:  # type: ignore[type-arg]
        return self._get_status(task) in _TERMINAL_STATUSES

    def _build_output(self, task: Task | dict, retrieval_status: str) -> dict:  # type: ignore[type-arg]
        """Build the output dict from a task."""
        if isinstance(task, Task):
            return {
                "retrieval_status": retrieval_status,
                "task": {
                    "task_id": task.task_id,
                    "task_type": task.task_type.value if hasattr(task.task_type, "value") else str(task.task_type),
                    "status": task.status.value if hasattr(task.status, "value") else str(task.status),
                    "description": task.description,
                    "output": task.metadata.get("output", ""),
                    "exit_code": task.metadata.get("exit_code"),
                    "error": task.metadata.get("error"),
                    "prompt": task.metadata.get("prompt"),
                    "result": task.metadata.get("result"),
                },
            }
        if isinstance(task, dict):
            return {
                "retrieval_status": retrieval_status,
                "task": {
                    "task_id": task.get("task_id", ""),
                    "task_type": task.get("task_type", "unknown"),
                    "status": task.get("status", "unknown"),
                    "description": task.get("description", ""),
                    "output": task.get("output", task.get("metadata", {}).get("output", "")),
                    "exit_code": task.get("exit_code"),
                    "error": task.get("error"),
                },
            }
        return {"retrieval_status": retrieval_status, "task": None}

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        inp: TaskOutputInput = args  # type: ignore[assignment]

        task = self._get_task_from_state(context, inp.task_id)
        if task is None:
            return ToolResult(
                data={
                    "retrieval_status": "not_found",
                    "task": None,
                    "error": f"Task not found: {inp.task_id}",
                }
            )

        # If not blocking or already terminal, return immediately
        if not inp.block or self._is_terminal(task):
            status = "success" if self._is_terminal(task) else "not_ready"
            return ToolResult(data=self._build_output(task, status))

        # Block: poll until complete or timeout
        timeout_s = inp.timeout / 1000.0
        elapsed = 0.0
        while elapsed < timeout_s:
            if context.abort_controller.is_set():
                break

            await asyncio.sleep(_POLL_INTERVAL_S)
            elapsed += _POLL_INTERVAL_S

            task = self._get_task_from_state(context, inp.task_id)
            if task is None:
                return ToolResult(
                    data={
                        "retrieval_status": "not_found",
                        "task": None,
                        "error": f"Task disappeared: {inp.task_id}",
                    }
                )
            if self._is_terminal(task):
                return ToolResult(data=self._build_output(task, "success"))

        # Timed out - return current state
        if task is not None:
            return ToolResult(data=self._build_output(task, "timeout"))
        return ToolResult(
            data={"retrieval_status": "timeout", "task": None}
        )

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        inp: TaskOutputInput = input  # type: ignore[assignment]
        return f"Getting output for task #{inp.task_id}"

    def is_read_only(self, input: BaseModel) -> bool:
        return True

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True
