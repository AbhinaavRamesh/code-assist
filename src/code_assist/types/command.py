"""Command types for slash commands.

Ports the TypeScript command types from src/types/command.ts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Literal, Protocol

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


# ---------------------------------------------------------------------------
# Command Result Types
# ---------------------------------------------------------------------------


@dataclass
class TextCommandResult:
    type: Literal["text"] = "text"
    value: str = ""


@dataclass
class CompactCommandResult:
    type: Literal["compact"] = "compact"
    compaction_result: dict[str, Any] = field(default_factory=dict)
    display_text: str | None = None


@dataclass
class SkipCommandResult:
    type: Literal["skip"] = "skip"


LocalCommandResult = TextCommandResult | CompactCommandResult | SkipCommandResult


# ---------------------------------------------------------------------------
# Command Availability
# ---------------------------------------------------------------------------


class CommandAvailability(StrEnum):
    CLAUDE_AI = "claude-ai"  # OAuth subscriber
    CONSOLE = "console"  # Console API key user


class CommandLoadedFrom(StrEnum):
    COMMANDS_DEPRECATED = "commands_DEPRECATED"
    SKILLS = "skills"
    PLUGIN = "plugin"
    MANAGED = "managed"
    BUNDLED = "bundled"
    MCP = "mcp"


class CommandType(StrEnum):
    LOCAL = "local"
    PROMPT = "prompt"
    LOCAL_JSX = "local-jsx"


class SettingSource(StrEnum):
    USER = "user"
    PROJECT = "project"
    LOCAL = "local"
    BUILTIN = "builtin"
    MCP = "mcp"
    PLUGIN = "plugin"
    BUNDLED = "bundled"
    MANAGED = "managed"


class CommandResultDisplay(StrEnum):
    SKIP = "skip"
    SYSTEM = "system"
    USER = "user"


class ResumeEntrypoint(StrEnum):
    CLI_FLAG = "cli_flag"
    SLASH_COMMAND_PICKER = "slash_command_picker"
    SLASH_COMMAND_SESSION_ID = "slash_command_session_id"
    SLASH_COMMAND_TITLE = "slash_command_title"
    FORK = "fork"


# ---------------------------------------------------------------------------
# Command Protocols
# ---------------------------------------------------------------------------


class LocalCommandModule(Protocol):
    """Protocol for a local command module."""

    async def call(self, args: str, context: Any) -> LocalCommandResult: ...


class PromptCommandModule(Protocol):
    """Protocol for a prompt command that expands to API query."""

    async def get_prompt_for_command(
        self, args: str, context: Any
    ) -> list[dict[str, Any]]: ...


# ---------------------------------------------------------------------------
# Command Data Classes
# ---------------------------------------------------------------------------


@dataclass
class CommandBase:
    """Base fields shared by all command types."""

    name: str = ""
    description: str = ""
    command_type: CommandType = CommandType.LOCAL
    has_user_specified_description: bool = False
    is_hidden: bool = False
    aliases: list[str] = field(default_factory=list)
    is_mcp: bool = False
    argument_hint: str | None = None
    when_to_use: str | None = None
    version: str | None = None
    disable_model_invocation: bool = False
    user_invocable: bool = True
    loaded_from: CommandLoadedFrom | None = None
    kind: str | None = None
    immediate: bool = False
    is_sensitive: bool = False
    availability: list[CommandAvailability] = field(default_factory=list)
    supports_non_interactive: bool = False
    disable_non_interactive: bool = False

    # For prompt commands
    progress_message: str = ""
    content_length: int = 0
    arg_names: list[str] | None = None
    allowed_tools: list[str] | None = None
    model: str | None = None
    source: str | None = None
    skill_root: str | None = None
    context: Literal["inline", "fork"] | None = None
    agent: str | None = None
    effort: str | None = None
    paths: list[str] | None = None

    def is_enabled(self) -> bool:
        """Check if this command is enabled."""
        return True

    def user_facing_name(self) -> str:
        """Get the user-facing display name."""
        return self.name


def get_command_name(cmd: CommandBase) -> str:
    """Get the canonical command name."""
    return cmd.name


def is_command_enabled(cmd: CommandBase) -> bool:
    """Check if a command is currently enabled."""
    return cmd.is_enabled()
