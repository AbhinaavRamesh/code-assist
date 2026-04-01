"""EnterPlanMode tool - switches the session into planning mode.

In plan mode the agent should focus on exploring the codebase and designing
an implementation approach. File writes are disallowed until the plan is
approved and ExitPlanMode is called.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

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

PLAN_MODE_INSTRUCTIONS = (
    "Entered plan mode. You should now focus on exploring the codebase "
    "and designing an implementation approach.\n\n"
    "In plan mode, you should:\n"
    "1. Thoroughly explore the codebase to understand existing patterns\n"
    "2. Identify similar features and architectural approaches\n"
    "3. Consider multiple approaches and their trade-offs\n"
    "4. Use AskUserQuestion if you need to clarify the approach\n"
    "5. Design a concrete implementation strategy\n"
    "6. When ready, use ExitPlanMode to present your plan for approval\n\n"
    "Remember: DO NOT write or edit any files yet. "
    "This is a read-only exploration and planning phase."
)


class EnterPlanModeInput(BaseModel):
    """Input schema for EnterPlanMode (no fields required)."""

    pass


class EnterPlanModeTool(ToolDef):
    """Switch the session into planning mode for structured reasoning.

    When plan mode is active, only read-only tools are permitted.
    The agent explores the codebase and designs an approach before executing.
    """

    name = "EnterPlanMode"
    search_hint = "switch to plan mode to design an approach before coding"
    max_result_size_chars = 100_000
    should_defer = True

    @property
    def input_schema(self) -> type[BaseModel]:
        return EnterPlanModeInput

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        # Plan mode cannot be used from sub-agent contexts
        if context.agent_id:
            return ValidationResult(
                result=False,
                message="EnterPlanMode cannot be used in agent contexts",
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
        if context.agent_id:
            return ToolResult(
                data={"error": "EnterPlanMode tool cannot be used in agent contexts"}
            )

        # Transition the permission mode to 'plan'
        def _enter_plan(state: Any) -> Any:
            if isinstance(state, dict):
                tpc = dict(state.get("toolPermissionContext", {}))
                # Save previous mode for ExitPlanMode to restore
                tpc["previousMode"] = tpc.get("mode", "default")
                tpc["mode"] = "plan"
                return {**state, "toolPermissionContext": tpc}
            return state

        context.set_app_state(_enter_plan)

        return ToolResult(
            data={"message": PLAN_MODE_INSTRUCTIONS}
        )

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        return "Requests permission to enter plan mode for complex tasks requiring exploration and design"

    def is_read_only(self, input: BaseModel) -> bool:
        return True

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True
