"""Tool progress data types.

Tool progress data types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal


# ---------------------------------------------------------------------------
# Tool Progress Data Types
# ---------------------------------------------------------------------------


@dataclass
class BashProgress:
    """Progress data for BashTool execution."""

    type: Literal["bash_progress"] = "bash_progress"
    output: str = ""
    command: str = ""
    is_complete: bool = False
    exit_code: int | None = None
    pid: int | None = None
    is_background: bool = False
    interrupted: bool = False
    timed_out: bool = False


@dataclass
class MCPProgress:
    """Progress data for MCP tool execution."""

    type: Literal["mcp_progress"] = "mcp_progress"
    server_name: str = ""
    tool_name: str = ""
    progress: float | None = None
    total: float | None = None
    message: str | None = None


@dataclass
class AgentToolProgress:
    """Progress data for AgentTool sub-agent execution."""

    type: Literal["agent_progress"] = "agent_progress"
    agent_id: str = ""
    agent_type: str = ""
    message: str = ""
    is_complete: bool = False
    content: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class WebSearchProgress:
    """Progress data for web search operations."""

    type: Literal["web_search_progress"] = "web_search_progress"
    query: str = ""
    results_count: int = 0
    is_complete: bool = False


@dataclass
class SkillToolProgress:
    """Progress data for skill tool execution."""

    type: Literal["skill_progress"] = "skill_progress"
    skill_name: str = ""
    message: str = ""
    is_complete: bool = False


@dataclass
class TaskOutputProgress:
    """Progress data for task output streaming."""

    type: Literal["task_output_progress"] = "task_output_progress"
    task_id: str = ""
    output: str = ""
    is_complete: bool = False


@dataclass
class REPLToolProgress:
    """Progress data for REPL tool execution."""

    type: Literal["repl_progress"] = "repl_progress"
    output: str = ""
    is_complete: bool = False


@dataclass
class GenericToolProgress:
    """Generic progress data for tools without specific progress types."""

    type: Literal["generic_progress"] = "generic_progress"
    message: str = ""
    progress: float | None = None
    total: float | None = None


# Union of all tool progress types
ToolProgressData = (
    BashProgress
    | MCPProgress
    | AgentToolProgress
    | WebSearchProgress
    | SkillToolProgress
    | TaskOutputProgress
    | REPLToolProgress
    | GenericToolProgress
)


# ---------------------------------------------------------------------------
# Tool Progress Wrapper
# ---------------------------------------------------------------------------


@dataclass
class ToolProgress:
    """Wraps tool progress data with a tool use ID."""

    tool_use_id: str = ""
    data: ToolProgressData = field(default_factory=GenericToolProgress)


# ---------------------------------------------------------------------------
# Spinner Mode
# ---------------------------------------------------------------------------


class SpinnerMode(StrEnum):
    THINKING = "thinking"
    TOOL_USE = "tool_use"
    STREAMING = "streaming"
    IDLE = "idle"
