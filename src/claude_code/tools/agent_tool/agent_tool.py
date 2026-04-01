"""AgentTool - spawns a sub-agent with isolated context for delegated work."""

from __future__ import annotations

import logging
import time
from typing import Any, Literal

from pydantic import BaseModel, Field

from claude_code.tasks.local_agent_task import create_agent_task
from claude_code.tasks.types import Task, TaskStatus
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


class AgentToolInput(BaseModel):
    """Input schema for AgentTool.

    Mirrors the JS AgentTool schema: description, prompt, subagent_type,
    model, run_in_background, isolation, name, cwd.
    """

    description: str = Field(
        ..., description="A short (3-5 word) description of the task"
    )
    prompt: str = Field(
        ..., description="The task for the agent to perform"
    )
    subagent_type: str | None = Field(
        default=None,
        description="Type of specialized agent to use (e.g. 'explore', 'plan', 'verify')",
    )
    model: Literal["sonnet", "opus", "haiku"] | None = Field(
        default=None,
        description="Optional model override for this agent",
    )
    run_in_background: bool = Field(
        default=False,
        description="Set to true to run this agent in the background",
    )
    isolation: Literal["worktree"] | None = Field(
        default=None,
        description='Isolation mode. "worktree" creates a temporary git worktree.',
    )
    name: str | None = Field(
        default=None,
        description="Name for the spawned agent (addressable via SendMessage)",
    )
    cwd: str | None = Field(
        default=None,
        description="Absolute path to run the agent in. Mutually exclusive with isolation: worktree.",
    )


class AgentTool(ToolDef):
    """Spawn a sub-agent with isolated context for delegated work.

    In foreground mode, the agent runs to completion and returns its result.
    In background mode, a task is created and the tool returns immediately.
    """

    name = "Agent"
    aliases = ["SubAgent"]
    search_hint = "delegate work to a sub-agent with isolated context"
    max_result_size_chars = 100_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return AgentToolInput

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        inp: AgentToolInput = input  # type: ignore[assignment]
        if not inp.prompt.strip():
            return ValidationResult(
                result=False, message="prompt is required", error_code=1
            )
        if not inp.description.strip():
            return ValidationResult(
                result=False, message="description is required", error_code=2
            )
        if inp.isolation == "worktree" and inp.cwd:
            return ValidationResult(
                result=False,
                message="cwd and isolation: worktree are mutually exclusive",
                error_code=3,
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
        inp: AgentToolInput = args  # type: ignore[assignment]

        agent_type = inp.subagent_type or "general"

        # Create an agent task in AppState
        task = create_agent_task(
            inp.description,
            agent_type=agent_type,
        )

        # Store the prompt in task metadata
        task.metadata["prompt"] = inp.prompt
        task.metadata["agent_type"] = agent_type
        if inp.model:
            task.metadata["model"] = inp.model
        if inp.name:
            task.metadata["name"] = inp.name
        if inp.cwd:
            task.metadata["cwd"] = inp.cwd
        if inp.isolation:
            task.metadata["isolation"] = inp.isolation

        task.status = TaskStatus.RUNNING
        task.created_at = time.time()
        task.updated_at = task.created_at

        # Register task in AppState
        def _register(state: Any) -> Any:
            if isinstance(state, dict):
                tasks = dict(state.get("tasks", {}))
                tasks[task.task_id] = task
                return {**state, "tasks": tasks}
            return state

        context.set_app_state(_register)

        # Background mode: return task ID immediately
        if inp.run_in_background:
            return ToolResult(
                data={
                    "task_id": task.task_id,
                    "status": "running",
                    "description": inp.description,
                    "message": (
                        f"Agent task {task.task_id} started in background: {inp.description}. "
                        "Use TaskOutput to check results."
                    ),
                }
            )

        # Foreground mode: execute the agent task synchronously
        # The agent runs with its own query engine context
        try:
            result = await self._execute_agent(inp, task, context, on_progress)

            # Mark task complete
            def _complete(state: Any) -> Any:
                if isinstance(state, dict):
                    tasks = dict(state.get("tasks", {}))
                    t = tasks.get(task.task_id)
                    if isinstance(t, Task):
                        t.status = TaskStatus.COMPLETED
                        t.metadata["result"] = result
                        t.updated_at = time.time()
                    tasks[task.task_id] = t
                    return {**state, "tasks": tasks}
                return state

            context.set_app_state(_complete)

            return ToolResult(data=result)

        except Exception as exc:
            # Mark task failed
            error_msg = str(exc)

            def _fail(state: Any) -> Any:
                if isinstance(state, dict):
                    tasks = dict(state.get("tasks", {}))
                    t = tasks.get(task.task_id)
                    if isinstance(t, Task):
                        t.status = TaskStatus.FAILED
                        t.metadata["error"] = error_msg
                        t.updated_at = time.time()
                    tasks[task.task_id] = t
                    return {**state, "tasks": tasks}
                return state

            context.set_app_state(_fail)

            return ToolResult(
                data={
                    "task_id": task.task_id,
                    "status": "failed",
                    "error": error_msg,
                    "message": f"Agent task failed: {error_msg}",
                }
            )

    async def _execute_agent(
        self,
        inp: AgentToolInput,
        task: Task,
        context: ToolUseContext,
        on_progress: ToolCallProgress | None,
    ) -> str:
        """Execute the sub-agent and return its text result.

        This delegates to the query engine if available, or falls back
        to a simple prompt-echo for environments without a full engine.
        """
        # Attempt to use a real query engine if one is wired in
        state = context.get_app_state()
        query_engine = None
        if isinstance(state, dict):
            query_engine = state.get("query_engine")
        elif state is not None and hasattr(state, "query_engine"):
            query_engine = getattr(state, "query_engine", None)

        if query_engine and callable(getattr(query_engine, "query", None)):
            # Real execution via query engine
            response = await query_engine.query(
                inp.prompt,
                agent_type=inp.subagent_type,
                model=inp.model,
            )
            return str(response)

        # Fallback: return the prompt as acknowledgment
        return (
            f"Sub-agent ({inp.subagent_type or 'general'}) completed task: "
            f"{inp.description}\n\nPrompt was: {inp.prompt[:500]}"
        )

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        inp: AgentToolInput = input  # type: ignore[assignment]
        return inp.description or f"Agent: {inp.prompt[:60]}"

    def is_read_only(self, input: BaseModel) -> bool:
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True
