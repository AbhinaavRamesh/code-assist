"""TeamCreate tool - creates a new multi-agent team.

Creates a team with the current agent as team lead. The team file is
persisted to disk and registered in AppState for inter-agent coordination.
"""

from __future__ import annotations

import logging
import os
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

logger = logging.getLogger(__name__)

TEAM_LEAD_NAME = "lead"


class TeamCreateInput(BaseModel):
    """Input schema for TeamCreate."""

    team_name: str = Field(
        ..., description="Name for the new team to create"
    )
    description: str | None = Field(
        default=None, description="Team description/purpose"
    )
    agent_type: str | None = Field(
        default=None,
        description="Type/role of the team lead (e.g. 'researcher', 'test-runner')",
    )


class TeamCreateTool(ToolDef):
    """Create a new multi-agent team for coordinated work.

    The creating agent becomes the team lead. Additional agents can be
    spawned as teammates via the Agent tool with team_name set.
    """

    name = "TeamCreate"
    search_hint = "create a multi-agent swarm team"
    max_result_size_chars = 100_000
    should_defer = True

    @property
    def input_schema(self) -> type[BaseModel]:
        return TeamCreateInput

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        inp: TeamCreateInput = input  # type: ignore[assignment]
        if not inp.team_name or not inp.team_name.strip():
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
        inp: TeamCreateInput = args  # type: ignore[assignment]

        state = context.get_app_state()

        # Check for existing team
        existing_team = None
        if isinstance(state, dict):
            tc = state.get("teamContext")
            if tc:
                existing_team = tc.get("teamName")

        if existing_team:
            return ToolResult(
                data={
                    "error": (
                        f'Already leading team "{existing_team}". '
                        "A leader can only manage one team at a time. "
                        "Use TeamDelete to end the current team first."
                    )
                }
            )

        # Generate lead agent ID
        lead_agent_id = f"{TEAM_LEAD_NAME}-{inp.team_name}"
        lead_agent_type = inp.agent_type or TEAM_LEAD_NAME

        # Build team context
        team_context: dict[str, Any] = {
            "teamName": inp.team_name,
            "description": inp.description,
            "leadAgentId": lead_agent_id,
            "createdAt": time.time(),
            "teammates": {
                lead_agent_id: {
                    "agentId": lead_agent_id,
                    "name": TEAM_LEAD_NAME,
                    "agentType": lead_agent_type,
                    "joinedAt": time.time(),
                    "cwd": os.getcwd(),
                },
            },
        }

        # Register in AppState
        def _create_team(prev: Any) -> Any:
            if isinstance(prev, dict):
                return {**prev, "teamContext": team_context}
            return prev

        context.set_app_state(_create_team)

        return ToolResult(
            data={
                "team_name": inp.team_name,
                "lead_agent_id": lead_agent_id,
                "message": (
                    f"Team '{inp.team_name}' created. "
                    f"You are the team lead ({lead_agent_id}). "
                    "Use the Agent tool to spawn teammates."
                ),
            }
        )

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        inp: TeamCreateInput = input  # type: ignore[assignment]
        return f"Creating team: {inp.team_name}"

    def is_read_only(self, input: BaseModel) -> bool:
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return False
