"""Tool base types and protocols.

Tool base types and protocols.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel

from code_assist.types.message import AssistantMessage, Message
from code_assist.types.permissions import (
    PermissionResult,
    ToolPermissionContext,
)
from code_assist.types.tools import ToolProgress, ToolProgressData


# ---------------------------------------------------------------------------
# Tool Input JSON Schema (raw dict form for MCP tools)
# ---------------------------------------------------------------------------

ToolInputJSONSchema = dict[str, Any]


# ---------------------------------------------------------------------------
# Tool Result
# ---------------------------------------------------------------------------


@dataclass
class ToolResult:
    """Result from executing a tool."""

    data: Any = None
    new_messages: list[Message] | None = None
    context_modifier: Callable[["ToolUseContext"], "ToolUseContext"] | None = None
    mcp_meta: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Validation Result
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    """Result of tool input validation."""

    result: bool = True
    message: str = ""
    error_code: int = 0


# ---------------------------------------------------------------------------
# Description Options
# ---------------------------------------------------------------------------


@dataclass
class DescriptionOptions:
    """Options passed to tool.description()."""

    is_non_interactive_session: bool = False
    tool_permission_context: ToolPermissionContext = field(
        default_factory=lambda: ToolPermissionContext()
    )
    tools: list[Any] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Search/Read Classification
# ---------------------------------------------------------------------------


@dataclass
class SearchOrReadInfo:
    """Whether a tool use is a search, read, or list operation."""

    is_search: bool = False
    is_read: bool = False
    is_list: bool = False


# ---------------------------------------------------------------------------
# Tool Use Context
# ---------------------------------------------------------------------------


@dataclass
class ToolUseContext:
    """Context provided to tools during execution.

    Context provided to tools during execution.
    """

    # Core options
    commands: list[Any] = field(default_factory=list)
    debug: bool = False
    main_loop_model: str = ""
    tools: list["Tool"] = field(default_factory=list)
    verbose: bool = False
    mcp_clients: list[Any] = field(default_factory=list)
    mcp_resources: dict[str, list[Any]] = field(default_factory=dict)
    is_non_interactive_session: bool = False
    agent_definitions: Any = None
    max_budget_usd: float | None = None
    custom_system_prompt: str | None = None
    append_system_prompt: str | None = None
    query_source: str | None = None
    refresh_tools: Callable[[], list["Tool"]] | None = None

    # Abort control
    abort_controller: asyncio.Event = field(default_factory=asyncio.Event)

    # State access
    _get_app_state: Callable[[], Any] | None = None
    _set_app_state: Callable[[Callable[[Any], Any]], None] | None = None

    # Messages
    messages: list[Message] = field(default_factory=list)

    # File state
    read_file_state: dict[str, Any] = field(default_factory=dict)

    # Callbacks
    set_in_progress_tool_use_ids: Callable[
        [Callable[[set[str]], set[str]]], None
    ] | None = None
    set_response_length: Callable[[Callable[[int], int]], None] | None = None
    update_file_history_state: Callable[[Callable[[Any], Any]], None] | None = None
    update_attribution_state: Callable[[Callable[[Any], Any]], None] | None = None

    # Agent info
    agent_id: str | None = None
    agent_type: str | None = None
    tool_use_id: str | None = None

    # Limits
    file_reading_limits: dict[str, int] | None = None
    glob_limits: dict[str, int] | None = None

    def get_app_state(self) -> Any:
        """Get the current application state."""
        if self._get_app_state:
            return self._get_app_state()
        return None

    def set_app_state(self, updater: Callable[[Any], Any]) -> None:
        """Update the application state."""
        if self._set_app_state:
            self._set_app_state(updater)


# ---------------------------------------------------------------------------
# Tool Call Progress Callback
# ---------------------------------------------------------------------------

ToolCallProgress = Callable[[ToolProgress], None]

# Type for the canUseTool function
CanUseToolFn = Callable[..., Any]


# ---------------------------------------------------------------------------
# Tool Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class Tool(Protocol):
    """Protocol defining the interface for all tools.

    Protocol defining the interface for all tools.
    Each tool implementation must satisfy this protocol.
    """

    @property
    def name(self) -> str:
        """Tool name (unique identifier)."""
        ...

    @property
    def max_result_size_chars(self) -> int:
        """Maximum result size before disk persistence."""
        ...

    @property
    def input_schema(self) -> type[BaseModel]:
        """Pydantic model for input validation (replaces Zod schema)."""
        ...

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        """Execute the tool with the given arguments."""
        ...

    async def description(
        self,
        input: BaseModel,
        options: DescriptionOptions,
    ) -> str:
        """Generate a description for the tool use."""
        ...

    def is_enabled(self) -> bool:
        """Whether this tool is currently available."""
        ...

    def is_read_only(self, input: BaseModel) -> bool:
        """Whether this invocation is read-only."""
        ...

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        """Whether this tool can run concurrently with others."""
        ...


# ---------------------------------------------------------------------------
# Tool Definition (concrete base class)
# ---------------------------------------------------------------------------


class ToolDef:
    """Concrete base class for tool implementations.

    Provides sensible defaults for optional Tool protocol methods.
    Subclasses should override the required methods.
    """

    name: str = ""
    aliases: list[str] = []
    search_hint: str | None = None
    max_result_size_chars: int = 100_000
    should_defer: bool = False
    always_load: bool = False
    is_mcp: bool = False
    is_lsp: bool = False
    strict: bool = False

    @property
    def input_schema(self) -> type[BaseModel]:
        """Override in subclass to provide input schema."""
        return BaseModel

    def input_json_schema(self) -> ToolInputJSONSchema | None:
        """Optional raw JSON schema (for MCP tools)."""
        return None

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        """Override in subclass."""
        raise NotImplementedError

    async def description(
        self,
        input: BaseModel,
        options: DescriptionOptions,
    ) -> str:
        """Override in subclass to provide description."""
        return f"Using {self.name}"

    async def prompt(self, **kwargs: Any) -> str:
        """Generate the prompt/system description for this tool."""
        return ""

    def is_enabled(self) -> bool:
        """Whether the tool is currently enabled."""
        return True

    def is_read_only(self, input: BaseModel) -> bool:
        """Whether this invocation is read-only."""
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        """Whether this tool can run concurrently with others."""
        return True

    def is_destructive(self, input: BaseModel) -> bool:
        """Whether this invocation performs irreversible operations."""
        return False

    def interrupt_behavior(self) -> Literal["cancel", "block"]:
        """What to do when user submits while this tool is running."""
        return "block"

    def is_search_or_read_command(self, input: BaseModel) -> SearchOrReadInfo:
        """Whether this is a search/read operation for UI collapsing."""
        return SearchOrReadInfo()

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        """Validate input before permission check."""
        return ValidationResult(result=True)

    async def check_permissions(
        self, input: BaseModel, context: ToolUseContext
    ) -> PermissionResult | None:
        """Tool-specific permission check."""
        return None

    def backfill_observable_input(self, input: dict[str, Any]) -> None:
        """Mutate input copy before observers see it."""
        pass


# ---------------------------------------------------------------------------
# Tool Utilities
# ---------------------------------------------------------------------------


def tool_matches_name(
    tool: Tool | ToolDef,
    name: str,
) -> bool:
    """Check if a tool matches the given name (primary name or alias)."""
    if tool.name == name:
        return True
    aliases = getattr(tool, "aliases", [])
    return name in aliases


def find_tool_by_name(
    tools: list[Tool | ToolDef],
    name: str,
) -> Tool | ToolDef | None:
    """Find a tool by name or alias."""
    for tool in tools:
        if tool_matches_name(tool, name):
            return tool
    return None


Tools = list[Tool | ToolDef]
