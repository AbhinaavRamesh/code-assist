"""ExitPlanMode tool - exits planning mode and restores the previous permission mode.

The agent presents its plan for user approval and then returns to the
previous permission mode (typically 'default' or 'auto') so that file
writes are re-enabled.
"""

from __future__ import annotations

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


class AllowedPrompt(BaseModel):
    """A prompt-based permission request."""

    tool: str = Field(
        default="Bash", description="The tool this prompt applies to"
    )
    prompt: str = Field(
        ...,
        description='Semantic description of the action, e.g. "run tests"',
    )


class ExitPlanModeInput(BaseModel):
    """Input schema for ExitPlanMode."""

    allowed_prompts: list[AllowedPrompt] | None = Field(
        default=None,
        description="Prompt-based permissions needed to implement the plan",
    )


class ExitPlanModeTool(ToolDef):
    """Exit plan mode, present the plan, and restore the previous permission mode.

    The agent should have completed its exploration and designed an approach.
    After exiting, file writes are re-enabled.
    """

    name = "ExitPlanMode"
    search_hint = "exit plan mode and present implementation plan for approval"
    max_result_size_chars = 100_000
    should_defer = True

    @property
    def input_schema(self) -> type[BaseModel]:
        return ExitPlanModeInput

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        # Verify we are actually in plan mode
        state = context.get_app_state()
        if isinstance(state, dict):
            tpc = state.get("toolPermissionContext", {})
            mode = tpc.get("mode", "default")
            if mode != "plan":
                return ValidationResult(
                    result=False,
                    message="Not currently in plan mode. Use EnterPlanMode first.",
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
        inp: ExitPlanModeInput = args  # type: ignore[assignment]

        # Restore previous permission mode
        restored_mode = "default"

        def _exit_plan(state: Any) -> Any:
            nonlocal restored_mode
            if isinstance(state, dict):
                tpc = dict(state.get("toolPermissionContext", {}))
                restored_mode = tpc.pop("previousMode", "default")
                tpc["mode"] = restored_mode

                # Apply allowed prompts if provided
                if inp.allowed_prompts:
                    existing = list(tpc.get("allowedPrompts", []))
                    for ap in inp.allowed_prompts:
                        existing.append({"tool": ap.tool, "prompt": ap.prompt})
                    tpc["allowedPrompts"] = existing

                return {**state, "toolPermissionContext": tpc}
            return state

        context.set_app_state(_exit_plan)

        allowed_count = len(inp.allowed_prompts) if inp.allowed_prompts else 0
        msg = (
            f"Exited plan mode. Permission mode restored to '{restored_mode}'. "
            "You can now implement the plan."
        )
        if allowed_count > 0:
            msg += f" {allowed_count} prompt-based permission(s) registered."

        return ToolResult(data={"message": msg, "mode": restored_mode})

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        return "Exiting plan mode and presenting implementation plan"

    def is_read_only(self, input: BaseModel) -> bool:
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return False
