"""Tool registry - assembles all available tools.

Tool registry - assembles all available tools.
"""

from __future__ import annotations

from claude_code.config.constants import is_feature_enabled
from claude_code.tools.base import ToolDef, Tools


def get_all_tools() -> Tools:
    """Get all registered tools.

    Tools are lazily imported and conditionally included based on feature flags.
    This function is called once at startup and when tools need refreshing.
    """
    tools: Tools = []

    # Core tools (always enabled)
    # These will be populated as tools are implemented in subsequent branches
    # Branch 06: FileRead, FileWrite, FileEdit, NotebookEdit
    # Branch 07: Bash
    # Branch 08: Glob, Grep, WebFetch, WebSearch, ToolSearch
    # Branch 15: MCPTool, ListMcpResources, ReadMcpResource
    # Branch 16: AgentTool, SendMessage, TeamCreate, TeamDelete
    # Branch 17: TaskCreate, TaskGet, TaskUpdate, TaskList, TaskStop, TaskOutput
    # Branch 22: SkillTool
    # Branch 23: LSPTool
    # Branch 24: EnterWorktree, ExitWorktree
    # Branch 25: EnterPlanMode, ExitPlanMode, TodoWrite, ConfigTool, AskUser, Cron tools

    return tools


def get_tool_names(tools: Tools) -> list[str]:
    """Get the names of all tools."""
    return [t.name for t in tools]


def filter_enabled_tools(tools: Tools) -> Tools:
    """Filter tools to only enabled ones."""
    return [t for t in tools if t.is_enabled()]
