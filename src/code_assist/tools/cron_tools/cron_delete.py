"""CronDelete tool - deletes a scheduled cron job."""

from __future__ import annotations

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


class CronDeleteInput(BaseModel):
    """Input schema for CronDelete."""

    cron_id: str = Field(..., description="ID of the cron job to delete")


class CronDeleteTool(ToolDef):
    """Delete a scheduled cron job by ID.

    Removes the job from AppState so it will no longer be executed.
    """

    name = "CronDelete"
    max_result_size_chars = 10_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return CronDeleteInput

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        inp: CronDeleteInput = input  # type: ignore[assignment]
        if not inp.cron_id.strip():
            return ValidationResult(
                result=False, message="cron_id is required", error_code=1
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
        inp: CronDeleteInput = args  # type: ignore[assignment]

        # Look up in AppState
        state = context.get_app_state()
        cron_jobs: dict[str, Any] = {}
        if isinstance(state, dict):
            cron_jobs = state.get("cron_jobs", {})

        if inp.cron_id not in cron_jobs:
            return ToolResult(
                data={"error": f"Cron job not found: {inp.cron_id}"}
            )

        # Remove from AppState
        def _remove(prev: Any) -> Any:
            if isinstance(prev, dict):
                jobs = dict(prev.get("cron_jobs", {}))
                jobs.pop(inp.cron_id, None)
                return {**prev, "cron_jobs": jobs}
            return prev

        context.set_app_state(_remove)

        return ToolResult(
            data={
                "id": inp.cron_id,
                "message": f"Cron job {inp.cron_id} deleted.",
            }
        )

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        inp: CronDeleteInput = input  # type: ignore[assignment]
        return f"Deleting cron job {inp.cron_id}"

    def is_read_only(self, input: BaseModel) -> bool:
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True
