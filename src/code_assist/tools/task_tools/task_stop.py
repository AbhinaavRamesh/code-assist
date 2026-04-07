"""TaskStop tool - stops a running task via AppState and process kill."""

from __future__ import annotations

from pydantic import BaseModel, Field

from code_assist.tasks.stop_task import stop_task
from code_assist.tasks.types import Task, TaskStatus
from code_assist.tools.base import (
    CanUseToolFn,
    DescriptionOptions,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
    ValidationResult,
)
from code_assist.types.message import AssistantMessage


class TaskStopInput(BaseModel):
    """Input schema for TaskStop."""

    task_id: str = Field(..., description="ID of the task to stop")


class TaskStopTool(ToolDef):
    """Stop a running task by killing its process and updating AppState."""

    name = "TaskStop"
    max_result_size_chars = 10_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return TaskStopInput

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        inp: TaskStopInput = input  # type: ignore[assignment]
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
        inp: TaskStopInput = args  # type: ignore[assignment]

        state = context.get_app_state()
        tasks: dict = {}  # type: ignore[type-arg]
        if isinstance(state, dict):
            tasks = state.get("tasks", {})
        elif state is not None and hasattr(state, "tasks"):
            tasks = getattr(state, "tasks", {})

        task = tasks.get(inp.task_id)
        if task is None:
            return ToolResult(
                data={"error": f"Task not found: {inp.task_id}"}
            )

        # Determine current status
        if isinstance(task, Task):
            current_status = task.status
        elif isinstance(task, dict):
            current_status = TaskStatus(task.get("status", "pending"))
        else:
            return ToolResult(
                data={"error": f"Unknown task format for {inp.task_id}"}
            )

        if current_status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
            return ToolResult(
                data={
                    "task_id": inp.task_id,
                    "status": current_status.value,
                    "message": f"Task {inp.task_id} is already {current_status.value}, cannot stop.",
                }
            )

        # Attempt to kill the process
        killed = False
        if isinstance(task, Task):
            killed = stop_task(task)
        elif isinstance(task, dict):
            # Build a temporary Task object for stop_task
            temp_task = Task(
                task_id=inp.task_id,
                status=current_status,
                metadata=task.get("metadata", {}),
            )
            killed = stop_task(temp_task)

        # Update AppState
        def _stop(prev_state: dict) -> dict:  # type: ignore[type-arg]
            prev_tasks = dict(prev_state.get("tasks", {}))
            t = prev_tasks.get(inp.task_id)
            if t is None:
                return prev_state
            if isinstance(t, Task):
                t.status = TaskStatus.KILLED
            elif isinstance(t, dict):
                t["status"] = "killed"
            prev_tasks[inp.task_id] = t
            return {**prev_state, "tasks": prev_tasks}

        context.set_app_state(_stop)

        return ToolResult(
            data={
                "task_id": inp.task_id,
                "killed": killed,
                "message": f"Task {inp.task_id} stopped.",
            }
        )

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        inp: TaskStopInput = input  # type: ignore[assignment]
        return f"Stopping task #{inp.task_id}"

    def is_read_only(self, input: BaseModel) -> bool:
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True
