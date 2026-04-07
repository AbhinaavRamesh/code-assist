"""Comprehensive tests for all tool implementations.

Covers instantiation, input schema validation, and basic call behavior
for every tool. Uses a mock ToolUseContext with in-memory AppState.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from code_assist.tools.base import (
    CanUseToolFn,
    DescriptionOptions,
    ToolDef,
    ToolResult,
    ToolUseContext,
)
from code_assist.types.message import AssistantMessage


# ---------------------------------------------------------------------------
# Helpers: mock context with in-memory AppState
# ---------------------------------------------------------------------------


def _make_context(**overrides: Any) -> ToolUseContext:
    """Build a ToolUseContext with an in-memory dict AppState."""
    state: dict[str, Any] = overrides.pop("state", {"tasks": {}, "todos": {}})

    def _get() -> dict[str, Any]:
        return state

    def _set(updater):  # type: ignore[no-untyped-def]
        nonlocal state
        state = updater(state)

    ctx = ToolUseContext(
        _get_app_state=_get,
        _set_app_state=_set,
        **overrides,
    )
    return ctx


def _make_parent_msg() -> AssistantMessage:
    return AssistantMessage(content=[])


def _noop_can_use(*_a: Any, **_kw: Any) -> Any:
    return True


# ---------------------------------------------------------------------------
# Task tools
# ---------------------------------------------------------------------------


class TestTaskCreateTool:
    def test_instantiation(self) -> None:
        from code_assist.tools.task_tools.task_create import TaskCreateTool
        tool = TaskCreateTool()
        assert tool.name == "TaskCreate"

    @pytest.mark.asyncio
    async def test_create_task(self) -> None:
        from code_assist.tools.task_tools.task_create import TaskCreateInput, TaskCreateTool
        tool = TaskCreateTool()
        ctx = _make_context()
        inp = TaskCreateInput(subject="Build feature", description="Implement X")
        result = await tool.call(inp, ctx, _noop_can_use, _make_parent_msg())
        assert isinstance(result, ToolResult)
        assert result.data["task_id"]
        assert result.data["subject"] == "Build feature"
        # Task should be in AppState
        state = ctx.get_app_state()
        assert result.data["task_id"] in state["tasks"]

    @pytest.mark.asyncio
    async def test_validation_empty_subject(self) -> None:
        from code_assist.tools.task_tools.task_create import TaskCreateInput, TaskCreateTool
        tool = TaskCreateTool()
        ctx = _make_context()
        inp = TaskCreateInput(subject="  ", description="test")
        v = await tool.validate_input(inp, ctx)
        assert not v.result


class TestTaskGetTool:
    @pytest.mark.asyncio
    async def test_not_found(self) -> None:
        from code_assist.tools.task_tools.task_get import TaskGetInput, TaskGetTool
        tool = TaskGetTool()
        ctx = _make_context()
        inp = TaskGetInput(task_id="nonexistent")
        result = await tool.call(inp, ctx, _noop_can_use, _make_parent_msg())
        assert "error" in result.data

    @pytest.mark.asyncio
    async def test_found(self) -> None:
        from code_assist.tools.task_tools.task_create import TaskCreateInput, TaskCreateTool
        from code_assist.tools.task_tools.task_get import TaskGetInput, TaskGetTool
        ctx = _make_context()
        # Create a task first
        create = TaskCreateTool()
        created = await create.call(
            TaskCreateInput(subject="Test"), ctx, _noop_can_use, _make_parent_msg()
        )
        tid = created.data["task_id"]
        # Now get it
        get_tool = TaskGetTool()
        result = await get_tool.call(
            TaskGetInput(task_id=tid), ctx, _noop_can_use, _make_parent_msg()
        )
        assert result.data["subject"] == "Test"


class TestTaskUpdateTool:
    @pytest.mark.asyncio
    async def test_update_status(self) -> None:
        from code_assist.tools.task_tools.task_create import TaskCreateInput, TaskCreateTool
        from code_assist.tools.task_tools.task_update import TaskUpdateInput, TaskUpdateTool
        ctx = _make_context()
        created = await TaskCreateTool().call(
            TaskCreateInput(subject="X"), ctx, _noop_can_use, _make_parent_msg()
        )
        tid = created.data["task_id"]
        result = await TaskUpdateTool().call(
            TaskUpdateInput(task_id=tid, status="running"),
            ctx, _noop_can_use, _make_parent_msg(),
        )
        assert "status=running" in result.data["message"]


class TestTaskListTool:
    @pytest.mark.asyncio
    async def test_empty(self) -> None:
        from code_assist.tools.task_tools.task_list import TaskListInput, TaskListTool
        tool = TaskListTool()
        ctx = _make_context()
        result = await tool.call(TaskListInput(), ctx, _noop_can_use, _make_parent_msg())
        assert result.data["tasks"] == []

    @pytest.mark.asyncio
    async def test_lists_created_tasks(self) -> None:
        from code_assist.tools.task_tools.task_create import TaskCreateInput, TaskCreateTool
        from code_assist.tools.task_tools.task_list import TaskListInput, TaskListTool
        ctx = _make_context()
        await TaskCreateTool().call(
            TaskCreateInput(subject="A"), ctx, _noop_can_use, _make_parent_msg()
        )
        await TaskCreateTool().call(
            TaskCreateInput(subject="B"), ctx, _noop_can_use, _make_parent_msg()
        )
        result = await TaskListTool().call(
            TaskListInput(), ctx, _noop_can_use, _make_parent_msg()
        )
        assert result.data["count"] == 2


class TestTaskStopTool:
    @pytest.mark.asyncio
    async def test_stop_not_found(self) -> None:
        from code_assist.tools.task_tools.task_stop import TaskStopInput, TaskStopTool
        tool = TaskStopTool()
        ctx = _make_context()
        result = await tool.call(
            TaskStopInput(task_id="nope"), ctx, _noop_can_use, _make_parent_msg()
        )
        assert "error" in result.data


class TestTaskOutputTool:
    @pytest.mark.asyncio
    async def test_not_found(self) -> None:
        from code_assist.tools.task_tools.task_output import TaskOutputInput, TaskOutputTool
        tool = TaskOutputTool()
        ctx = _make_context()
        result = await tool.call(
            TaskOutputInput(task_id="missing", block=False),
            ctx, _noop_can_use, _make_parent_msg(),
        )
        assert result.data["retrieval_status"] == "not_found"


# ---------------------------------------------------------------------------
# Agent tool
# ---------------------------------------------------------------------------


class TestAgentTool:
    def test_instantiation(self) -> None:
        from code_assist.tools.agent_tool.agent_tool import AgentTool
        tool = AgentTool()
        assert tool.name == "Agent"

    @pytest.mark.asyncio
    async def test_background_mode(self) -> None:
        from code_assist.tools.agent_tool.agent_tool import AgentTool, AgentToolInput
        tool = AgentTool()
        ctx = _make_context()
        inp = AgentToolInput(
            description="Test agent",
            prompt="Do something",
            run_in_background=True,
        )
        result = await tool.call(inp, ctx, _noop_can_use, _make_parent_msg())
        assert result.data["status"] == "running"
        assert result.data["task_id"]

    @pytest.mark.asyncio
    async def test_foreground_mode(self) -> None:
        from code_assist.tools.agent_tool.agent_tool import AgentTool, AgentToolInput
        tool = AgentTool()
        ctx = _make_context()
        inp = AgentToolInput(description="Test", prompt="Hello world")
        result = await tool.call(inp, ctx, _noop_can_use, _make_parent_msg())
        # Should return a result (fallback string)
        assert isinstance(result.data, str)

    @pytest.mark.asyncio
    async def test_validation_empty_prompt(self) -> None:
        from code_assist.tools.agent_tool.agent_tool import AgentTool, AgentToolInput
        tool = AgentTool()
        ctx = _make_context()
        inp = AgentToolInput(description="Test", prompt="  ")
        v = await tool.validate_input(inp, ctx)
        assert not v.result


# ---------------------------------------------------------------------------
# Plan mode tools
# ---------------------------------------------------------------------------


class TestEnterPlanModeTool:
    @pytest.mark.asyncio
    async def test_enter_plan_mode(self) -> None:
        from code_assist.tools.plan_mode.enter_plan_mode import EnterPlanModeInput, EnterPlanModeTool
        tool = EnterPlanModeTool()
        ctx = _make_context(state={"toolPermissionContext": {"mode": "default"}})
        result = await tool.call(
            EnterPlanModeInput(), ctx, _noop_can_use, _make_parent_msg()
        )
        assert "plan mode" in result.data["message"].lower()
        state = ctx.get_app_state()
        assert state["toolPermissionContext"]["mode"] == "plan"

    @pytest.mark.asyncio
    async def test_blocked_in_agent_context(self) -> None:
        from code_assist.tools.plan_mode.enter_plan_mode import EnterPlanModeInput, EnterPlanModeTool
        tool = EnterPlanModeTool()
        ctx = _make_context(agent_id="sub-1")
        v = await tool.validate_input(EnterPlanModeInput(), ctx)
        assert not v.result


class TestExitPlanModeTool:
    @pytest.mark.asyncio
    async def test_exit_plan_mode(self) -> None:
        from code_assist.tools.plan_mode.exit_plan_mode import ExitPlanModeInput, ExitPlanModeTool
        tool = ExitPlanModeTool()
        ctx = _make_context(
            state={"toolPermissionContext": {"mode": "plan", "previousMode": "default"}}
        )
        result = await tool.call(
            ExitPlanModeInput(), ctx, _noop_can_use, _make_parent_msg()
        )
        assert result.data["mode"] == "default"
        state = ctx.get_app_state()
        assert state["toolPermissionContext"]["mode"] == "default"


# ---------------------------------------------------------------------------
# AskUserQuestion tool
# ---------------------------------------------------------------------------


class TestAskUserQuestionTool:
    @pytest.mark.asyncio
    async def test_with_answers(self) -> None:
        from code_assist.tools.ask_user.ask_user_question import (
            AskUserQuestionInput,
            AskUserQuestionTool,
            Question,
            QuestionOption,
        )
        tool = AskUserQuestionTool()
        ctx = _make_context()
        inp = AskUserQuestionInput(
            questions=[
                Question(
                    question="Which approach?",
                    header="Approach",
                    options=[
                        QuestionOption(label="A", description="Option A"),
                        QuestionOption(label="B", description="Option B"),
                    ],
                )
            ],
            answers={"Which approach?": "A"},
        )
        result = await tool.call(inp, ctx, _noop_can_use, _make_parent_msg())
        assert result.data["answers"]["Which approach?"] == "A"

    @pytest.mark.asyncio
    async def test_uniqueness_validation(self) -> None:
        from code_assist.tools.ask_user.ask_user_question import (
            AskUserQuestionInput,
            AskUserQuestionTool,
            Question,
            QuestionOption,
        )
        tool = AskUserQuestionTool()
        ctx = _make_context()
        inp = AskUserQuestionInput(
            questions=[
                Question(
                    question="Same?",
                    header="H1",
                    options=[
                        QuestionOption(label="X", description="d"),
                        QuestionOption(label="Y", description="d"),
                    ],
                ),
                Question(
                    question="Same?",  # duplicate
                    header="H2",
                    options=[
                        QuestionOption(label="A", description="d"),
                        QuestionOption(label="B", description="d"),
                    ],
                ),
            ]
        )
        v = await tool.validate_input(inp, ctx)
        assert not v.result


# ---------------------------------------------------------------------------
# MCP tool
# ---------------------------------------------------------------------------


class TestMCPTool:
    def test_instantiation(self) -> None:
        from code_assist.tools.mcp_tool.mcp_tool import MCPTool
        tool = MCPTool()
        assert tool.is_mcp is True

    @pytest.mark.asyncio
    async def test_server_not_found(self) -> None:
        from code_assist.tools.mcp_tool.mcp_tool import MCPTool, MCPToolInput
        tool = MCPTool()
        ctx = _make_context()
        inp = MCPToolInput(server_name="fake", tool_name="test", arguments={})
        result = await tool.call(inp, ctx, _noop_can_use, _make_parent_msg())
        assert "not found" in str(result.data).lower()


# ---------------------------------------------------------------------------
# Skill tool
# ---------------------------------------------------------------------------


class TestSkillTool:
    @pytest.mark.asyncio
    async def test_skill_not_found(self) -> None:
        from code_assist.tools.skill_tool.skill_tool import SkillTool, SkillToolInput
        tool = SkillTool()
        ctx = _make_context()
        inp = SkillToolInput(skill="nonexistent-skill-xyz")
        result = await tool.call(inp, ctx, _noop_can_use, _make_parent_msg())
        assert "error" in result.data or "not found" in str(result.data).lower()


# ---------------------------------------------------------------------------
# Worktree tools
# ---------------------------------------------------------------------------


class TestEnterWorktreeTool:
    def test_instantiation(self) -> None:
        from code_assist.tools.worktree.enter_worktree import EnterWorktreeTool
        tool = EnterWorktreeTool()
        assert tool.name == "EnterWorktree"

    @pytest.mark.asyncio
    async def test_invalid_slug(self) -> None:
        from code_assist.tools.worktree.enter_worktree import EnterWorktreeInput, EnterWorktreeTool
        tool = EnterWorktreeTool()
        ctx = _make_context()
        inp = EnterWorktreeInput(name="invalid name with spaces!!!")
        v = await tool.validate_input(inp, ctx)
        assert not v.result


class TestExitWorktreeTool:
    @pytest.mark.asyncio
    async def test_not_in_worktree(self) -> None:
        from code_assist.tools.worktree.exit_worktree import ExitWorktreeInput, ExitWorktreeTool
        tool = ExitWorktreeTool()
        ctx = _make_context()
        v = await tool.validate_input(ExitWorktreeInput(action="keep"), ctx)
        assert not v.result


# ---------------------------------------------------------------------------
# SendMessage tool
# ---------------------------------------------------------------------------


class TestSendMessageTool:
    @pytest.mark.asyncio
    async def test_direct_message(self) -> None:
        from code_assist.tools.send_message.send_message_tool import SendMessageInput, SendMessageTool
        tool = SendMessageTool()
        ctx = _make_context(state={"mailboxes": {}})
        inp = SendMessageInput(to="alice", message="Hello!", summary="Greet")
        result = await tool.call(inp, ctx, _noop_can_use, _make_parent_msg())
        assert result.data["success"] is True
        # Check mailbox
        state = ctx.get_app_state()
        assert len(state["mailboxes"]["alice"]) == 1

    @pytest.mark.asyncio
    async def test_broadcast_no_teammates(self) -> None:
        from code_assist.tools.send_message.send_message_tool import SendMessageInput, SendMessageTool
        tool = SendMessageTool()
        ctx = _make_context(state={"mailboxes": {}})
        inp = SendMessageInput(to="*", message="Hello all!")
        result = await tool.call(inp, ctx, _noop_can_use, _make_parent_msg())
        assert result.data["success"] is False


# ---------------------------------------------------------------------------
# Team tools
# ---------------------------------------------------------------------------


class TestTeamCreateTool:
    @pytest.mark.asyncio
    async def test_create_team(self) -> None:
        from code_assist.tools.team_tools.team_create import TeamCreateInput, TeamCreateTool
        tool = TeamCreateTool()
        ctx = _make_context()
        inp = TeamCreateInput(team_name="alpha", description="Test team")
        result = await tool.call(inp, ctx, _noop_can_use, _make_parent_msg())
        assert result.data["team_name"] == "alpha"
        state = ctx.get_app_state()
        assert state["teamContext"]["teamName"] == "alpha"

    @pytest.mark.asyncio
    async def test_duplicate_team(self) -> None:
        from code_assist.tools.team_tools.team_create import TeamCreateInput, TeamCreateTool
        tool = TeamCreateTool()
        ctx = _make_context()
        await tool.call(
            TeamCreateInput(team_name="t1"), ctx, _noop_can_use, _make_parent_msg()
        )
        result = await tool.call(
            TeamCreateInput(team_name="t2"), ctx, _noop_can_use, _make_parent_msg()
        )
        assert "error" in result.data


class TestTeamDeleteTool:
    @pytest.mark.asyncio
    async def test_no_team(self) -> None:
        from code_assist.tools.team_tools.team_delete import TeamDeleteInput, TeamDeleteTool
        tool = TeamDeleteTool()
        ctx = _make_context()
        result = await tool.call(
            TeamDeleteInput(team_name="x"), ctx, _noop_can_use, _make_parent_msg()
        )
        assert "error" in result.data


# ---------------------------------------------------------------------------
# Config tool
# ---------------------------------------------------------------------------


class TestConfigTool:
    @pytest.mark.asyncio
    async def test_get_unknown(self) -> None:
        from code_assist.tools.config_tool.config_tool import ConfigTool, ConfigToolInput
        tool = ConfigTool()
        ctx = _make_context()
        result = await tool.call(
            ConfigToolInput(setting="unknown_setting"),
            ctx, _noop_can_use, _make_parent_msg(),
        )
        assert result.data["success"] is False

    @pytest.mark.asyncio
    async def test_get_theme(self) -> None:
        from code_assist.tools.config_tool.config_tool import ConfigTool, ConfigToolInput
        tool = ConfigTool()
        ctx = _make_context()
        result = await tool.call(
            ConfigToolInput(setting="theme"),
            ctx, _noop_can_use, _make_parent_msg(),
        )
        assert result.data["success"] is True
        assert result.data["operation"] == "get"

    def test_is_read_only_for_get(self) -> None:
        from code_assist.tools.config_tool.config_tool import ConfigTool, ConfigToolInput
        tool = ConfigTool()
        assert tool.is_read_only(ConfigToolInput(setting="theme")) is True
        assert tool.is_read_only(ConfigToolInput(setting="theme", value="dark")) is False


# ---------------------------------------------------------------------------
# TodoWrite tool
# ---------------------------------------------------------------------------


class TestTodoWriteTool:
    @pytest.mark.asyncio
    async def test_write_todos(self) -> None:
        from code_assist.tools.todo_write.todo_write_tool import TodoItem, TodoWriteInput, TodoWriteTool
        tool = TodoWriteTool()
        ctx = _make_context(state={"todos": {}})
        inp = TodoWriteInput(
            todos=[
                TodoItem(id="1", status="pending", content="Task A"),
                TodoItem(id="2", status="completed", content="Task B"),
            ]
        )
        result = await tool.call(inp, ctx, _noop_can_use, _make_parent_msg())
        assert len(result.data["newTodos"]) == 2
        assert result.data["summary"]["completed"] == 1

    @pytest.mark.asyncio
    async def test_all_done_clears(self) -> None:
        from code_assist.tools.todo_write.todo_write_tool import TodoItem, TodoWriteInput, TodoWriteTool
        tool = TodoWriteTool()
        ctx = _make_context(state={"todos": {}})
        inp = TodoWriteInput(
            todos=[
                TodoItem(id="1", status="completed", content="Done"),
            ]
        )
        await tool.call(inp, ctx, _noop_can_use, _make_parent_msg())
        state = ctx.get_app_state()
        assert state["todos"]["session"] == []


# ---------------------------------------------------------------------------
# Cron tools
# ---------------------------------------------------------------------------


class TestCronCreateTool:
    @pytest.mark.asyncio
    async def test_create_cron(self) -> None:
        from code_assist.tools.cron_tools.cron_create import CronCreateInput, CronCreateTool
        tool = CronCreateTool()
        ctx = _make_context(state={"cron_jobs": {}})
        inp = CronCreateInput(schedule="*/5 * * * *", command="echo hello")
        result = await tool.call(inp, ctx, _noop_can_use, _make_parent_msg())
        assert result.data["id"].startswith("cron-")
        state = ctx.get_app_state()
        assert len(state["cron_jobs"]) == 1

    @pytest.mark.asyncio
    async def test_invalid_cron_expression(self) -> None:
        from code_assist.tools.cron_tools.cron_create import CronCreateInput, CronCreateTool
        tool = CronCreateTool()
        ctx = _make_context()
        inp = CronCreateInput(schedule="bad", command="test")
        v = await tool.validate_input(inp, ctx)
        assert not v.result


class TestCronDeleteTool:
    @pytest.mark.asyncio
    async def test_delete_not_found(self) -> None:
        from code_assist.tools.cron_tools.cron_delete import CronDeleteInput, CronDeleteTool
        tool = CronDeleteTool()
        ctx = _make_context(state={"cron_jobs": {}})
        result = await tool.call(
            CronDeleteInput(cron_id="nope"), ctx, _noop_can_use, _make_parent_msg()
        )
        assert "error" in result.data


class TestCronListTool:
    @pytest.mark.asyncio
    async def test_empty_list(self) -> None:
        from code_assist.tools.cron_tools.cron_list import CronListInput, CronListTool
        tool = CronListTool()
        ctx = _make_context(state={"cron_jobs": {}})
        result = await tool.call(
            CronListInput(), ctx, _noop_can_use, _make_parent_msg()
        )
        assert result.data["jobs"] == []


# ---------------------------------------------------------------------------
# LSP tool
# ---------------------------------------------------------------------------


class TestLSPTool:
    def test_instantiation(self) -> None:
        from code_assist.tools.lsp_tool.lsp_tool import LSPTool
        tool = LSPTool()
        assert tool.is_lsp is True

    @pytest.mark.asyncio
    async def test_no_lsp_server(self, tmp_path) -> None:
        from code_assist.tools.lsp_tool.lsp_tool import LSPTool, LSPToolInput
        tool = LSPTool()
        ctx = _make_context()
        # Create a real file for the test
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        inp = LSPToolInput(operation="hover", file_path=str(test_file), line=1, character=1)
        result = await tool.call(inp, ctx, _noop_can_use, _make_parent_msg())
        # Tool returns result even without LSP server
        assert result.data is not None


# ---------------------------------------------------------------------------
# Registry integration
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_all_tools_importable(self) -> None:
        from code_assist.tools.registry import get_all_tools
        tools = get_all_tools()
        assert len(tools) >= 33
        names = [t.name for t in tools]
        for expected in [
            "TaskCreate", "TaskGet", "TaskUpdate", "TaskList",
            "TaskStop", "TaskOutput", "Agent", "EnterPlanMode",
            "ExitPlanMode", "AskUserQuestion", "MCPTool", "Skill",
            "EnterWorktree", "ExitWorktree", "SendMessage",
            "TeamCreate", "TeamDelete", "Config", "TodoWrite",
            "CronCreate", "CronDelete", "CronList", "LSP",
        ]:
            assert expected in names, f"{expected} missing from registry"

    def test_no_duplicate_names(self) -> None:
        from code_assist.tools.registry import get_all_tools
        tools = get_all_tools()
        names = [t.name for t in tools]
        assert len(names) == len(set(names)), f"Duplicate names: {[n for n in names if names.count(n) > 1]}"
