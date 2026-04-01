"""TeamDelete tool - deletes a team and cleans up resources.

Removes the team context from AppState and optionally stops all
running teammate tasks.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

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

logger = logging.getLogger(__name__)


class TeamDeleteInput(BaseModel):
    """Input schema for TeamDelete."""

    team_name: str = Field(
        ..., description="Name of the team to delete"
    )
    force: bool = Field(
        default=False,
        description="Force delete even if teammates are still running",
    )


class TeamDeleteTool(ToolDef):
    """Delete a team and clean up its resources.

    Removes the team context from AppState. If force=True, running
    teammate tasks are stopped as well.
    """

    name = "TeamDelete"
    search_hint = "delete a multi-agent swarm team"
    max_result_size_chars = 10_000
    should_defer = True

    @property
    def input_schema(self) -> type[BaseModel]:
        return TeamDeleteInput

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        inp: TeamDeleteInput = input  # type: ignore[assignment]
        if not inp.team_name.strip():
            return ValidationResult(
                result=False,
                message="team_name is required",
                error_code=1,
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
        inp: TeamDeleteInput = args  # type: ignore[assignment]

        state = context.get_app_state()
        team_ctx = None
        if isinstance(state, dict):
            team_ctx = state.get("teamContext")

        if team_ctx is None:
            return ToolResult(
                data={"error": "No active team context found."}
            )

        current_name = team_ctx.get("teamName", "")
        if current_name != inp.team_name:
            return ToolResult(
                data={
                    "error": (
                        f"Team '{inp.team_name}' does not match current team "
                        f"'{current_name}'."
                    )
                }
            )

        # Count running teammates
        teammates = team_ctx.get("teammates", {})
        running_count = len(teammates)

        if running_count > 1 and not inp.force:
            return ToolResult(
                data={
                    "error": (
                        f"Team has {running_count} member(s). "
                        "Set force=true to delete, or stop teammates first."
                    ),
                    "member_count": running_count,
                }
            )

        # Remove team context from AppState
        def _delete_team(prev: Any) -> Any:
            if isinstance(prev, dict):
                new = {**prev}
                new.pop("teamContext", None)
                return new
            return prev

        context.set_app_state(_delete_team)

        return ToolResult(
            data={
                "team_name": inp.team_name,
                "members_removed": running_count,
                "message": f"Team '{inp.team_name}' deleted.",
            }
        )

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        inp: TeamDeleteInput = input  # type: ignore[assignment]
        return f"Deleting team: {inp.team_name}"

    def is_read_only(self, input: BaseModel) -> bool:
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return False
