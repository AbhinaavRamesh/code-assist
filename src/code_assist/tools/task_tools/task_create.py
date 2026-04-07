"""TaskCreate tool - creates a new background task in AppState."""

from __future__ import annotations

import time

from pydantic import BaseModel, Field

from code_assist.tasks.types import (
    Task,
    TaskStatus,
    TaskType,
    generate_task_id,
)
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


class TaskCreateInput(BaseModel):
    """Input schema for TaskCreate."""

    subject: str = Field(..., description="Brief task title")
    description: str = Field(default="", description="What needs to be done")
    task_type: str = Field(
        default="local_bash",
        description="Task type: local_bash, local_agent, or remote_agent",
    )
    active_form: str | None = Field(
        default=None, description="Present continuous form for spinner display"
    )
    owner: str | None = Field(
        default=None, description="Agent ID that owns this task"
    )


# Map of string type names to TaskType enum values
_TYPE_MAP = {
    "local_bash": TaskType.LOCAL_BASH,
    "local_agent": TaskType.LOCAL_AGENT,
    "remote_agent": TaskType.REMOTE_AGENT,
    "in_process_teammate": TaskType.IN_PROCESS_TEAMMATE,
    "local_workflow": TaskType.LOCAL_WORKFLOW,
}


class TaskCreateTool(ToolDef):
    """Create a new background task and register it in AppState."""

    name = "TaskCreate"
    max_result_size_chars = 10_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return TaskCreateInput

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        inp: TaskCreateInput = input  # type: ignore[assignment]
        if not inp.subject.strip():
            return ValidationResult(
                result=False, message="subject is required", error_code=1
            )
        if inp.task_type not in _TYPE_MAP:
            return ValidationResult(
                result=False,
                message=f"Unknown task_type: {inp.task_type}",
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
        inp: TaskCreateInput = args  # type: ignore[assignment]

        task_type = _TYPE_MAP.get(inp.task_type, TaskType.LOCAL_BASH)
        task_id = generate_task_id(task_type)
        now = time.time()

        task = Task(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            subject=inp.subject,
            description=inp.description,
            active_form=inp.active_form,
            owner=inp.owner or context.agent_id,
            created_at=now,
            updated_at=now,
        )

        # Register task in AppState
        def _add_task(state: dict) -> dict:  # type: ignore[type-arg]
            tasks = dict(state.get("tasks", {}))
            tasks[task_id] = task
            return {**state, "tasks": tasks}

        context.set_app_state(_add_task)

        return ToolResult(
            data={
                "task_id": task_id,
                "task_type": task_type.value,
                "status": task.status.value,
                "subject": task.subject,
                "message": f"Task {task_id} created: {task.subject}",
            }
        )

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        inp: TaskCreateInput = input  # type: ignore[assignment]
        return f"Creating task: {inp.subject}"

    def is_read_only(self, input: BaseModel) -> bool:
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True
