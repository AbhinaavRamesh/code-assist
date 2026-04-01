"""TodoWrite tool - manages a session-scoped todo/checklist.

Replaces the entire todo list atomically. Used by the model to track
progress on multi-step tasks. Each todo item has an id, status, and content.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from claude_code.tools.base import (
    CanUseToolFn,
    DescriptionOptions,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
)
from claude_code.types.message import AssistantMessage


class TodoItem(BaseModel):
    """A single todo item."""

    id: str = Field(..., description="Unique identifier for the todo item")
    status: Literal["pending", "in_progress", "completed"] = Field(
        ..., description="Status: pending, in_progress, or completed"
    )
    content: str = Field(..., description="Description of the todo item")
    priority: Literal["high", "medium", "low"] | None = Field(
        default=None, description="Optional priority level"
    )


class TodoWriteInput(BaseModel):
    """Input schema for TodoWrite."""

    todos: list[TodoItem] = Field(
        ..., description="The complete updated todo list"
    )


class TodoWriteTool(ToolDef):
    """Write or update a session-scoped todo list for tracking progress.

    The entire list is replaced atomically. When all items are completed,
    the list is cleared. The tool returns the old and new state for the
    model to understand what changed.
    """

    name = "TodoWrite"
    search_hint = "manage the session task checklist"
    max_result_size_chars = 100_000
    strict = True
    should_defer = True

    @property
    def input_schema(self) -> type[BaseModel]:
        return TodoWriteInput

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        inp: TodoWriteInput = args  # type: ignore[assignment]

        # Determine the todo key (agent-scoped or session-scoped)
        todo_key = context.agent_id or "session"

        # Get old todos from AppState
        state = context.get_app_state()
        old_todos: list[dict[str, Any]] = []
        if isinstance(state, dict):
            all_todos = state.get("todos", {})
            old_todos = all_todos.get(todo_key, [])

        # If all items are completed, clear the list
        all_done = all(t.status == "completed" for t in inp.todos)
        new_todos = [] if all_done else [t.model_dump() for t in inp.todos]

        # Check if verification nudge is needed
        verification_nudge = False
        if (
            all_done
            and len(inp.todos) >= 3
            and not context.agent_id
            and not any("verif" in t.content.lower() for t in inp.todos)
        ):
            verification_nudge = True

        # Update AppState
        serialized_new = [t.model_dump() for t in inp.todos]

        def _update_todos(prev: Any) -> Any:
            if isinstance(prev, dict):
                todos = dict(prev.get("todos", {}))
                todos[todo_key] = new_todos
                return {**prev, "todos": todos}
            return prev

        context.set_app_state(_update_todos)

        # Build summary
        completed = sum(1 for t in inp.todos if t.status == "completed")
        pending = sum(1 for t in inp.todos if t.status == "pending")
        in_progress = sum(1 for t in inp.todos if t.status == "in_progress")

        result: dict[str, Any] = {
            "oldTodos": old_todos,
            "newTodos": serialized_new,
            "summary": {
                "total": len(inp.todos),
                "completed": completed,
                "pending": pending,
                "in_progress": in_progress,
            },
        }

        if verification_nudge:
            result["verificationNudgeNeeded"] = True

        return ToolResult(data=result)

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        inp: TodoWriteInput = input  # type: ignore[assignment]
        return f"Updating {len(inp.todos)} todo item(s)"

    def is_read_only(self, input: BaseModel) -> bool:
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True
