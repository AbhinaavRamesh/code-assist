"""Tool registry - assembles all available tools."""

from __future__ import annotations

from claude_code.tools.base import ToolDef, Tools


def get_all_tools() -> Tools:
    """Get all registered tools."""
    # --- Existing tools ---
    from claude_code.tools.bash.bash_tool import BashTool
    from claude_code.tools.file_edit.file_edit_tool import FileEditTool
    from claude_code.tools.file_read.file_read_tool import FileReadTool
    from claude_code.tools.file_write.file_write_tool import FileWriteTool
    from claude_code.tools.glob_tool.glob_tool import GlobTool
    from claude_code.tools.grep_tool.grep_tool import GrepTool
    from claude_code.tools.notebook_edit.notebook_edit_tool import NotebookEditTool
    from claude_code.tools.tool_search.tool_search_tool import ToolSearchTool
    from claude_code.tools.web_fetch.web_fetch_tool import WebFetchTool
    from claude_code.tools.web_search.web_search_tool import WebSearchTool

    # --- Task tools ---
    from claude_code.tools.task_tools.task_create import TaskCreateTool
    from claude_code.tools.task_tools.task_get import TaskGetTool
    from claude_code.tools.task_tools.task_list import TaskListTool
    from claude_code.tools.task_tools.task_output import TaskOutputTool
    from claude_code.tools.task_tools.task_stop import TaskStopTool
    from claude_code.tools.task_tools.task_update import TaskUpdateTool

    # --- Agent tool ---
    from claude_code.tools.agent_tool.agent_tool import AgentTool

    # --- Plan mode tools ---
    from claude_code.tools.plan_mode.enter_plan_mode import EnterPlanModeTool
    from claude_code.tools.plan_mode.exit_plan_mode import ExitPlanModeTool

    # --- Ask user tool ---
    from claude_code.tools.ask_user.ask_user_question import AskUserQuestionTool

    # --- MCP tool ---
    from claude_code.tools.mcp_tool.mcp_tool import MCPTool

    # --- Skill tool ---
    from claude_code.tools.skill_tool.skill_tool import SkillTool

    # --- Worktree tools ---
    from claude_code.tools.worktree.enter_worktree import EnterWorktreeTool
    from claude_code.tools.worktree.exit_worktree import ExitWorktreeTool

    # --- Send message tool ---
    from claude_code.tools.send_message.send_message_tool import SendMessageTool

    # --- Team tools ---
    from claude_code.tools.team_tools.team_create import TeamCreateTool
    from claude_code.tools.team_tools.team_delete import TeamDeleteTool

    # --- Config tool ---
    from claude_code.tools.config_tool.config_tool import ConfigTool

    # --- Todo write tool ---
    from claude_code.tools.todo_write.todo_write_tool import TodoWriteTool

    # --- Cron tools ---
    from claude_code.tools.cron_tools.cron_create import CronCreateTool
    from claude_code.tools.cron_tools.cron_delete import CronDeleteTool
    from claude_code.tools.cron_tools.cron_list import CronListTool

    # --- LSP tool ---
    from claude_code.tools.lsp_tool.lsp_tool import LSPTool

    tools: Tools = [
        # Filesystem tools
        FileReadTool(),
        FileWriteTool(),
        FileEditTool(),
        NotebookEditTool(),
        # Execution
        BashTool(),
        # Search
        GlobTool(),
        GrepTool(),
        # Web
        WebFetchTool(),
        WebSearchTool(),
        # Discovery
        ToolSearchTool(),
        # Task management
        TaskCreateTool(),
        TaskGetTool(),
        TaskUpdateTool(),
        TaskListTool(),
        TaskStopTool(),
        TaskOutputTool(),
        # Agent
        AgentTool(),
        # Plan mode
        EnterPlanModeTool(),
        ExitPlanModeTool(),
        # User interaction
        AskUserQuestionTool(),
        # MCP
        MCPTool(),
        # Skills
        SkillTool(),
        # Worktree
        EnterWorktreeTool(),
        ExitWorktreeTool(),
        # Messaging
        SendMessageTool(),
        # Teams
        TeamCreateTool(),
        TeamDeleteTool(),
        # Configuration
        ConfigTool(),
        # Todo
        TodoWriteTool(),
        # Cron
        CronCreateTool(),
        CronDeleteTool(),
        CronListTool(),
        # LSP
        LSPTool(),
    ]

    return tools


def get_tool_names(tools: Tools) -> list[str]:
    """Get the names of all tools."""
    return [t.name for t in tools]


def filter_enabled_tools(tools: Tools) -> Tools:
    """Filter tools to only enabled ones."""
    return [t for t in tools if t.is_enabled()]
