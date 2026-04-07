"""TaskUpdate tool - updates a task's status or metadata in AppState."""

from __future__ import annotations

import time

from pydantic import BaseModel, Field

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

_VALID_STATUSES = {s.value for s in TaskStatus}


class TaskUpdateInput(BaseModel):
    """Input schema for TaskUpdate."""

    task_id: str = Field(..., description="ID of the task to update")
    status: str | None = Field(
        default=None,
        description="New status: pending, running, completed, failed, killed",
    )
    subject: str | None = Field(default=None, description="Updated task title")
    description: str | None = Field(
        default=None, description="Updated task description"
    )
    owner: str | None = Field(
        default=None, description="Updated owner agent ID"
    )
    blocks: list[str] | None = Field(
        default=None, description="Task IDs this task blocks"
    )
    blocked_by: list[str] | None = Field(
        default=None, description="Task IDs blocking this task"
    )


class TaskUpdateTool(ToolDef):
    """Update a task's status or metadata in AppState."""

    name = "TaskUpdate"
    max_result_size_chars = 10_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return TaskUpdateInput

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        inp: TaskUpdateInput = input  # type: ignore[assignment]
        if not inp.task_id.strip():
            return ValidationResult(
                result=False, message="task_id is required", error_code=1
            )
        if inp.status is not None and inp.status not in _VALID_STATUSES:
            return ValidationResult(
                result=False,
                message=f"Invalid status '{inp.status}'. Must be one of: {', '.join(sorted(_VALID_STATUSES))}",
                error_code=2,
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
        inp: TaskUpdateInput = args  # type: ignore[assignment]

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

        # Apply updates
        changes: list[str] = []

        def _update_task(prev_state: dict) -> dict:  # type: ignore[type-arg]
            prev_tasks = dict(prev_state.get("tasks", {}))
            t = prev_tasks.get(inp.task_id)
            if t is None:
                return prev_state

            if isinstance(t, Task):
                if inp.status is not None:
                    t.status = TaskStatus(inp.status)
                    changes.append(f"status={inp.status}")
                if inp.subject is not None:
                    t.subject = inp.subject
                    changes.append(f"subject={inp.subject}")
                if inp.description is not None:
                    t.description = inp.description
                    changes.append("description updated")
                if inp.owner is not None:
                    t.owner = inp.owner
                    changes.append(f"owner={inp.owner}")
                if inp.blocks is not None:
                    t.blocks = inp.blocks
                    changes.append(f"blocks={inp.blocks}")
                if inp.blocked_by is not None:
                    t.blocked_by = inp.blocked_by
                    changes.append(f"blocked_by={inp.blocked_by}")
                t.updated_at = time.time()
                prev_tasks[inp.task_id] = t
            elif isinstance(t, dict):
                if inp.status is not None:
                    t["status"] = inp.status
                    changes.append(f"status={inp.status}")
                if inp.subject is not None:
                    t["subject"] = inp.subject
                    changes.append(f"subject={inp.subject}")
                if inp.description is not None:
                    t["description"] = inp.description
                    changes.append("description updated")
                if inp.owner is not None:
                    t["owner"] = inp.owner
                    changes.append(f"owner={inp.owner}")
                if inp.blocks is not None:
                    t["blocks"] = inp.blocks
                    changes.append(f"blocks={inp.blocks}")
                if inp.blocked_by is not None:
                    t["blocked_by"] = inp.blocked_by
                    changes.append(f"blocked_by={inp.blocked_by}")
                t["updated_at"] = time.time()
                prev_tasks[inp.task_id] = t

            return {**prev_state, "tasks": prev_tasks}

        context.set_app_state(_update_task)

        summary = ", ".join(changes) if changes else "no fields changed"
        return ToolResult(
            data={
                "task_id": inp.task_id,
                "updated": changes,
                "message": f"Task {inp.task_id} updated: {summary}",
            }
        )

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        inp: TaskUpdateInput = input  # type: ignore[assignment]
        return f"Updating task #{inp.task_id}"

    def is_read_only(self, input: BaseModel) -> bool:
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True
