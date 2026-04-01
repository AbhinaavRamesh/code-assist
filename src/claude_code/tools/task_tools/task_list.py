"""TaskList tool - lists all tasks from AppState."""

from __future__ import annotations

from pydantic import BaseModel, Field

from claude_code.tasks.types import Task
from claude_code.tools.base import (
    CanUseToolFn,
    DescriptionOptions,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
)
from claude_code.types.message import AssistantMessage


class TaskListInput(BaseModel):
    """Input schema for TaskList."""

    status_filter: str | None = Field(
        default=None,
        description="Optional status to filter by: pending, running, completed, failed, killed",
    )


class TaskListTool(ToolDef):
    """List all active and completed tasks from AppState."""

    name = "TaskList"
    max_result_size_chars = 50_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return TaskListInput

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        inp: TaskListInput = args  # type: ignore[assignment]

        state = context.get_app_state()
        tasks: dict = {}  # type: ignore[type-arg]
        if isinstance(state, dict):
            tasks = state.get("tasks", {})
        elif state is not None and hasattr(state, "tasks"):
            tasks = getattr(state, "tasks", {})

        if not tasks:
            return ToolResult(data={"tasks": [], "message": "No tasks found."})

        result_list = []
        for task_id, task in tasks.items():
            if isinstance(task, Task):
                status_val = task.status.value if hasattr(task.status, "value") else str(task.status)
                entry = {
                    "task_id": task.task_id,
                    "task_type": task.task_type.value if hasattr(task.task_type, "value") else str(task.task_type),
                    "status": status_val,
                    "subject": task.subject,
                    "owner": task.owner,
                }
            elif isinstance(task, dict):
                status_val = task.get("status", "unknown")
                entry = {
                    "task_id": task.get("task_id", task_id),
                    "task_type": task.get("task_type", "unknown"),
                    "status": status_val,
                    "subject": task.get("subject", ""),
                    "owner": task.get("owner"),
                }
            else:
                continue

            # Apply status filter
            if inp.status_filter and status_val != inp.status_filter:
                continue

            result_list.append(entry)

        if not result_list:
            msg = "No tasks found"
            if inp.status_filter:
                msg += f" with status '{inp.status_filter}'"
            return ToolResult(data={"tasks": [], "message": msg + "."})

        return ToolResult(
            data={
                "tasks": result_list,
                "count": len(result_list),
                "message": f"Found {len(result_list)} task(s).",
            }
        )

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        return "Listing tasks"

    def is_read_only(self, input: BaseModel) -> bool:
        return True

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True
