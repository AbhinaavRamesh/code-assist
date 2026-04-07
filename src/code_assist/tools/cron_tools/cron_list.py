"""CronList tool - lists all scheduled cron jobs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from code_assist.tools.base import (
    CanUseToolFn,
    DescriptionOptions,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
)
from code_assist.types.message import AssistantMessage


class CronListInput(BaseModel):
    """Input schema for CronList (no required fields)."""

    pass


class CronListTool(ToolDef):
    """List all scheduled cron jobs from AppState."""

    name = "CronList"
    max_result_size_chars = 50_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return CronListInput

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        state = context.get_app_state()
        cron_jobs: dict[str, Any] = {}
        if isinstance(state, dict):
            cron_jobs = state.get("cron_jobs", {})

        if not cron_jobs:
            return ToolResult(
                data={"jobs": [], "message": "No cron jobs found."}
            )

        jobs_list = []
        for job_id, job in cron_jobs.items():
            if isinstance(job, dict):
                jobs_list.append({
                    "id": job.get("id", job_id),
                    "schedule": job.get("schedule", "?"),
                    "command": job.get("command", ""),
                    "description": job.get("description", ""),
                    "enabled": job.get("enabled", True),
                    "last_run": job.get("last_run"),
                })

        return ToolResult(
            data={
                "jobs": jobs_list,
                "count": len(jobs_list),
                "message": f"Found {len(jobs_list)} cron job(s).",
            }
        )

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        return "Listing cron jobs"

    def is_read_only(self, input: BaseModel) -> bool:
        return True

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True
