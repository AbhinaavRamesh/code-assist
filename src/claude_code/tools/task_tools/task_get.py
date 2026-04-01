"""TaskGet tool - retrieves a task by ID from AppState."""

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
    ValidationResult,
)
from claude_code.types.message import AssistantMessage


class TaskGetInput(BaseModel):
    """Input schema for TaskGet."""

    task_id: str = Field(..., description="ID of the task to retrieve")


def _task_to_dict(task: Task) -> dict:  # type: ignore[type-arg]
    """Serialize a Task to a dict for tool output."""
    return {
        "task_id": task.task_id,
        "task_type": task.task_type.value if hasattr(task.task_type, "value") else str(task.task_type),
        "status": task.status.value if hasattr(task.status, "value") else str(task.status),
        "subject": task.subject,
        "description": task.description,
        "active_form": task.active_form,
        "owner": task.owner,
        "blocks": task.blocks,
        "blocked_by": task.blocked_by,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


class TaskGetTool(ToolDef):
    """Retrieve the current state of a task from AppState."""

    name = "TaskGet"
    max_result_size_chars = 10_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return TaskGetInput

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        inp: TaskGetInput = input  # type: ignore[assignment]
        if not inp.task_id.strip():
            return ValidationResult(
                result=False, message="task_id is required", error_code=1
            )
        return ValidationResult(result=True)

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        inp: TaskGetInput = args  # type: ignore[assignment]

        state = context.get_app_state()
        tasks: dict = state.get("tasks", {}) if isinstance(state, dict) else {}  # type: ignore[type-arg]

        # Also try attribute-based access for dataclass AppState
        if not tasks and state is not None and hasattr(state, "tasks"):
            tasks = getattr(state, "tasks", {})

        task = tasks.get(inp.task_id)
        if task is None:
            return ToolResult(
                data={"error": f"Task not found: {inp.task_id}"}
            )

        if isinstance(task, Task):
            return ToolResult(data=_task_to_dict(task))

        # Already a dict (some AppState implementations store raw dicts)
        if isinstance(task, dict):
            return ToolResult(data=task)

        return ToolResult(data={"task_id": inp.task_id, "raw": str(task)})

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        inp: TaskGetInput = input  # type: ignore[assignment]
        return f"Getting task #{inp.task_id}"

    def is_read_only(self, input: BaseModel) -> bool:
        return True

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True
