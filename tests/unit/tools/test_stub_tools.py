"""Tests for all stub tool implementations.

Verifies each tool can be instantiated, has the correct name,
exposes a valid pydantic input schema, and implements the required methods.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from code_assist.tools.base import ToolDef


# ---------------------------------------------------------------------------
# Tool class imports
# ---------------------------------------------------------------------------

from code_assist.tools.task_tools.task_create import TaskCreateTool
from code_assist.tools.task_tools.task_get import TaskGetTool
from code_assist.tools.task_tools.task_update import TaskUpdateTool
from code_assist.tools.task_tools.task_list import TaskListTool
from code_assist.tools.task_tools.task_stop import TaskStopTool
from code_assist.tools.task_tools.task_output import TaskOutputTool
from code_assist.tools.agent_tool.agent_tool import AgentTool
from code_assist.tools.plan_mode.enter_plan_mode import EnterPlanModeTool
from code_assist.tools.plan_mode.exit_plan_mode import ExitPlanModeTool
from code_assist.tools.ask_user.ask_user_question import AskUserQuestionTool
from code_assist.tools.mcp_tool.mcp_tool import MCPTool
from code_assist.tools.skill_tool.skill_tool import SkillTool
from code_assist.tools.worktree.enter_worktree import EnterWorktreeTool
from code_assist.tools.worktree.exit_worktree import ExitWorktreeTool
from code_assist.tools.send_message.send_message_tool import SendMessageTool
from code_assist.tools.team_tools.team_create import TeamCreateTool
from code_assist.tools.team_tools.team_delete import TeamDeleteTool
from code_assist.tools.config_tool.config_tool import ConfigTool
from code_assist.tools.todo_write.todo_write_tool import TodoWriteTool
from code_assist.tools.cron_tools.cron_create import CronCreateTool
from code_assist.tools.cron_tools.cron_delete import CronDeleteTool
from code_assist.tools.cron_tools.cron_list import CronListTool
from code_assist.tools.lsp_tool.lsp_tool import LSPTool


# ---------------------------------------------------------------------------
# Parametrised test data: (ToolClass, expected_name)
# ---------------------------------------------------------------------------

TOOL_SPECS = [
    (TaskCreateTool, "TaskCreate"),
    (TaskGetTool, "TaskGet"),
    (TaskUpdateTool, "TaskUpdate"),
    (TaskListTool, "TaskList"),
    (TaskStopTool, "TaskStop"),
    (TaskOutputTool, "TaskOutput"),
    (AgentTool, "Agent"),
    (EnterPlanModeTool, "EnterPlanMode"),
    (ExitPlanModeTool, "ExitPlanMode"),
    (AskUserQuestionTool, "AskUserQuestion"),
    (MCPTool, "MCPTool"),
    (SkillTool, "Skill"),
    (EnterWorktreeTool, "EnterWorktree"),
    (ExitWorktreeTool, "ExitWorktree"),
    (SendMessageTool, "SendMessage"),
    (TeamCreateTool, "TeamCreate"),
    (TeamDeleteTool, "TeamDelete"),
    (ConfigTool, "Config"),
    (TodoWriteTool, "TodoWrite"),
    (CronCreateTool, "CronCreate"),
    (CronDeleteTool, "CronDelete"),
    (CronListTool, "CronList"),
    (LSPTool, "LSP"),
]


@pytest.mark.parametrize(
    "tool_cls, expected_name",
    TOOL_SPECS,
    ids=[name for _, name in TOOL_SPECS],
)
class TestStubTool:
    """Shared tests for every stub tool."""

    def test_instantiation(self, tool_cls: type[ToolDef], expected_name: str) -> None:
        """Tool can be instantiated without errors."""
        tool = tool_cls()
        assert tool is not None

    def test_name(self, tool_cls: type[ToolDef], expected_name: str) -> None:
        """Tool has the correct name attribute."""
        tool = tool_cls()
        assert tool.name == expected_name

    def test_is_tooldef_subclass(
        self, tool_cls: type[ToolDef], expected_name: str
    ) -> None:
        """Tool is a ToolDef subclass."""
        assert issubclass(tool_cls, ToolDef)

    def test_input_schema_is_pydantic(
        self, tool_cls: type[ToolDef], expected_name: str
    ) -> None:
        """input_schema property returns a pydantic BaseModel subclass."""
        tool = tool_cls()
        schema = tool.input_schema
        assert issubclass(schema, BaseModel)

    def test_has_call_method(
        self, tool_cls: type[ToolDef], expected_name: str
    ) -> None:
        """Tool has an async call method."""
        tool = tool_cls()
        assert hasattr(tool, "call")
        assert callable(tool.call)

    def test_has_description_method(
        self, tool_cls: type[ToolDef], expected_name: str
    ) -> None:
        """Tool has an async description method."""
        tool = tool_cls()
        assert hasattr(tool, "description")
        assert callable(tool.description)

    def test_is_read_only_defined(
        self, tool_cls: type[ToolDef], expected_name: str
    ) -> None:
        """Tool defines is_read_only."""
        tool = tool_cls()
        assert hasattr(tool, "is_read_only")
        assert callable(tool.is_read_only)

    def test_is_concurrency_safe_defined(
        self, tool_cls: type[ToolDef], expected_name: str
    ) -> None:
        """Tool defines is_concurrency_safe."""
        tool = tool_cls()
        assert hasattr(tool, "is_concurrency_safe")
        assert callable(tool.is_concurrency_safe)

    def test_max_result_size(
        self, tool_cls: type[ToolDef], expected_name: str
    ) -> None:
        """Tool has a positive max_result_size_chars."""
        tool = tool_cls()
        assert tool.max_result_size_chars > 0


class TestRegistryIncludesAllStubTools:
    """Verify the registry returns all stub tools."""

    def test_registry_contains_stub_tools(self) -> None:
        from code_assist.tools.registry import get_all_tools

        tools = get_all_tools()
        tool_names = {t.name for t in tools}
        expected_names = {name for _, name in TOOL_SPECS}
        missing = expected_names - tool_names
        assert not missing, f"Registry is missing tools: {missing}"

    def test_registry_tool_count(self) -> None:
        """Registry should have at least 10 existing + 23 new = 33 tools."""
        from code_assist.tools.registry import get_all_tools

        tools = get_all_tools()
        assert len(tools) >= 33
