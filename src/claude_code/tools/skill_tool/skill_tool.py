"""SkillTool - loads and executes named skills (slash commands).

Skills are prompt-based commands loaded from ~/.claude/skills/, bundled
skills, or MCP servers. They run in a forked sub-agent context with their
own token budget.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from claude_code.skills.load_skills_dir import load_skills
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


class SkillToolInput(BaseModel):
    """Input schema for SkillTool."""

    skill: str = Field(
        ...,
        description="The skill name to execute (e.g. 'commit', 'review-pr')",
    )
    args: str | None = Field(
        default=None,
        description="Optional arguments for the skill",
    )


class SkillTool(ToolDef):
    """Load and execute a named skill in a forked sub-agent context.

    Skills are discovered from:
    1. Bundled skills shipped with the package
    2. User skills in ~/.claude/skills/
    3. MCP prompt skills from connected servers

    The skill's prompt template is rendered and executed via a sub-agent
    query engine.
    """

    name = "Skill"
    search_hint = "run a skill or slash command"
    max_result_size_chars = 100_000
    should_defer = True

    @property
    def input_schema(self) -> type[BaseModel]:
        return SkillToolInput

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        inp: SkillToolInput = input  # type: ignore[assignment]
        if not inp.skill.strip():
            return ValidationResult(
                result=False, message="skill name is required", error_code=1
            )
        return ValidationResult(result=True)

    def _find_skill(
        self, skill_name: str, context: ToolUseContext
    ) -> dict[str, Any] | None:
        """Look up a skill by name from all available sources."""
        # Normalize: strip leading slash if present
        name = skill_name.lstrip("/").strip()

        # Check user/bundled skills
        all_skills = load_skills()
        for sk in all_skills:
            if sk.get("name", "").lower() == name.lower():
                return sk

        # Check MCP commands from AppState
        state = context.get_app_state()
        if isinstance(state, dict):
            mcp_commands = state.get("mcp", {}).get("commands", [])
            for cmd in mcp_commands:
                if isinstance(cmd, dict):
                    cmd_name = cmd.get("name", "")
                    if cmd_name.lower() == name.lower():
                        return cmd

        return None

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        inp: SkillToolInput = args  # type: ignore[assignment]

        skill = self._find_skill(inp.skill, context)
        if skill is None:
            # List available skills for helpful error
            available = load_skills()
            names = [s.get("name", "?") for s in available]
            return ToolResult(
                data={
                    "error": f"Skill not found: '{inp.skill}'",
                    "available_skills": names[:20],
                    "message": f"Unknown skill '{inp.skill}'. Available: {', '.join(names[:10])}",
                }
            )

        # Build the skill prompt
        skill_content = skill.get("content", "")
        skill_name = skill.get("name", inp.skill)

        # If the skill has argument placeholders, substitute them
        prompt = skill_content
        if inp.args and "$ARGUMENTS" in prompt:
            prompt = prompt.replace("$ARGUMENTS", inp.args)
        elif inp.args:
            prompt = f"{prompt}\n\nArguments: {inp.args}"

        # Execute via query engine if available
        state = context.get_app_state()
        query_engine = None
        if isinstance(state, dict):
            query_engine = state.get("query_engine")
        elif state is not None and hasattr(state, "query_engine"):
            query_engine = getattr(state, "query_engine", None)

        if query_engine and callable(getattr(query_engine, "query", None)):
            try:
                response = await query_engine.query(prompt, skill=skill_name)
                return ToolResult(
                    data={
                        "skill": skill_name,
                        "result": str(response),
                        "message": f"Skill '{skill_name}' completed.",
                    }
                )
            except Exception as exc:
                logger.warning("Skill execution failed: %s: %s", skill_name, exc)
                return ToolResult(
                    data={
                        "skill": skill_name,
                        "error": str(exc),
                        "message": f"Skill '{skill_name}' failed: {exc}",
                    }
                )

        # Fallback: return the skill content as instructions
        suffix = f" with args: {inp.args}" if inp.args else ""
        return ToolResult(
            data={
                "skill": skill_name,
                "content": prompt[:2000],
                "message": f"Loaded skill '{skill_name}'{suffix}. Follow the instructions in the content.",
            }
        )

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        inp: SkillToolInput = input  # type: ignore[assignment]
        return f"Running skill: {inp.skill}"

    def is_read_only(self, input: BaseModel) -> bool:
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return False
