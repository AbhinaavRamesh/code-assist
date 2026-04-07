"""CronCreate tool - creates a scheduled recurring task.

Scheduled tasks run on a cron expression and execute a command/prompt
at each interval.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic import BaseModel, Field

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

# Basic cron expression validation
_CRON_FIELDS = 5  # minute hour dom month dow


def _validate_cron_expr(expr: str) -> str | None:
    """Return an error message if the cron expression is invalid, else None."""
    parts = expr.strip().split()
    if len(parts) != _CRON_FIELDS:
        return f"Expected {_CRON_FIELDS} fields, got {len(parts)}"
    return None


class CronCreateInput(BaseModel):
    """Input schema for CronCreate."""

    schedule: str = Field(
        ...,
        description="Cron schedule expression (e.g. '*/5 * * * *' for every 5 minutes)",
    )
    command: str = Field(
        ..., description="Command or prompt to execute on schedule"
    )
    description: str | None = Field(
        default=None, description="Human-readable description of the job"
    )


class CronCreateTool(ToolDef):
    """Create a new scheduled cron job.

    The job is registered in AppState and executed by the scheduler service
    at each interval matching the cron expression.
    """

    name = "CronCreate"
    max_result_size_chars = 10_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return CronCreateInput

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        inp: CronCreateInput = input  # type: ignore[assignment]
        if not inp.schedule.strip():
            return ValidationResult(
                result=False, message="schedule is required", error_code=1
            )
        err = _validate_cron_expr(inp.schedule)
        if err:
            return ValidationResult(
                result=False,
                message=f"Invalid cron expression: {err}",
                error_code=2,
            )
        if not inp.command.strip():
            return ValidationResult(
                result=False, message="command is required", error_code=3
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
        inp: CronCreateInput = args  # type: ignore[assignment]

        cron_id = f"cron-{uuid.uuid4().hex[:8]}"
        now = time.time()

        job: dict[str, Any] = {
            "id": cron_id,
            "schedule": inp.schedule.strip(),
            "command": inp.command,
            "description": inp.description or inp.command[:50],
            "created_at": now,
            "enabled": True,
            "last_run": None,
            "next_run": None,
        }

        # Register in AppState
        def _add_cron(state: Any) -> Any:
            if isinstance(state, dict):
                crons = dict(state.get("cron_jobs", {}))
                crons[cron_id] = job
                return {**state, "cron_jobs": crons}
            return state

        context.set_app_state(_add_cron)

        return ToolResult(
            data={
                "id": cron_id,
                "schedule": inp.schedule.strip(),
                "command": inp.command,
                "message": f"Cron job {cron_id} created: schedule='{inp.schedule}', command='{inp.command[:50]}'",
            }
        )

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        inp: CronCreateInput = input  # type: ignore[assignment]
        return f"Creating cron job: {inp.schedule}"

    def is_read_only(self, input: BaseModel) -> bool:
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True
