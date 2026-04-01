"""Tests for tool base types, registry, and execution."""

import asyncio

import pytest
from pydantic import BaseModel, Field

from claude_code.tools.base import (
    DescriptionOptions,
    SearchOrReadInfo,
    ToolDef,
    ToolResult,
    ToolUseContext,
    ValidationResult,
    find_tool_by_name,
    tool_matches_name,
)
from claude_code.tools.registry import filter_enabled_tools, get_tool_names
from claude_code.types.message import AssistantMessage


# ---------------------------------------------------------------------------
# Test Tool Implementation
# ---------------------------------------------------------------------------


class EchoInput(BaseModel):
    message: str = Field(description="Message to echo")


class EchoTool(ToolDef):
    name = "echo"
    aliases = ["say"]
    max_result_size_chars = 10_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return EchoInput

    async def call(self, args, context, can_use_tool, parent_message, on_progress=None):
        return ToolResult(data=f"Echo: {args.message}")

    async def description(self, input, options):
        return f'echo "{input.message}"'

    def is_read_only(self, input):
        return True

    def is_concurrency_safe(self, input):
        return True


class DisabledTool(ToolDef):
    name = "disabled"
    max_result_size_chars = 1000

    def is_enabled(self):
        return False


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestToolDef:
    def test_tool_name(self) -> None:
        tool = EchoTool()
        assert tool.name == "echo"
        assert tool.aliases == ["say"]

    def test_tool_enabled(self) -> None:
        assert EchoTool().is_enabled() is True
        assert DisabledTool().is_enabled() is False

    def test_tool_defaults(self) -> None:
        tool = EchoTool()
        input_obj = EchoInput(message="hi")
        assert tool.is_read_only(input_obj) is True
        assert tool.is_concurrency_safe(input_obj) is True
        assert tool.is_destructive(input_obj) is False
        assert tool.interrupt_behavior() == "block"

    def test_search_or_read_info(self) -> None:
        tool = EchoTool()
        info = tool.is_search_or_read_command(EchoInput(message="x"))
        assert info.is_search is False
        assert info.is_read is False

    def test_validation_default(self) -> None:
        tool = EchoTool()
        result = asyncio.get_event_loop().run_until_complete(
            tool.validate_input(EchoInput(message="x"), ToolUseContext())
        )
        assert result.result is True


class TestToolMatching:
    def test_match_by_name(self) -> None:
        tool = EchoTool()
        assert tool_matches_name(tool, "echo") is True
        assert tool_matches_name(tool, "other") is False

    def test_match_by_alias(self) -> None:
        tool = EchoTool()
        assert tool_matches_name(tool, "say") is True

    def test_find_by_name(self) -> None:
        tools = [EchoTool(), DisabledTool()]
        found = find_tool_by_name(tools, "echo")
        assert found is not None
        assert found.name == "echo"

    def test_find_by_alias(self) -> None:
        tools = [EchoTool()]
        found = find_tool_by_name(tools, "say")
        assert found is not None

    def test_find_missing(self) -> None:
        tools = [EchoTool()]
        assert find_tool_by_name(tools, "nonexistent") is None


class TestToolRegistry:
    def test_get_tool_names(self) -> None:
        tools = [EchoTool(), DisabledTool()]
        names = get_tool_names(tools)
        assert names == ["echo", "disabled"]

    def test_filter_enabled(self) -> None:
        tools = [EchoTool(), DisabledTool()]
        enabled = filter_enabled_tools(tools)
        assert len(enabled) == 1
        assert enabled[0].name == "echo"


class TestToolExecution:
    @pytest.mark.asyncio
    async def test_execute_echo(self) -> None:
        tool = EchoTool()
        context = ToolUseContext()
        result = await tool.call(
            EchoInput(message="hello"),
            context,
            lambda *a, **kw: None,
            AssistantMessage(),
        )
        assert result.data == "Echo: hello"

    @pytest.mark.asyncio
    async def test_description(self) -> None:
        tool = EchoTool()
        desc = await tool.description(
            EchoInput(message="world"),
            DescriptionOptions(),
        )
        assert desc == 'echo "world"'


class TestToolUseContext:
    def test_default_context(self) -> None:
        ctx = ToolUseContext()
        assert ctx.debug is False
        assert ctx.messages == []
        assert ctx.agent_id is None

    def test_context_with_state(self) -> None:
        state = {"count": 0}
        ctx = ToolUseContext(
            _get_app_state=lambda: state,
            _set_app_state=lambda updater: None,
        )
        assert ctx.get_app_state() == state

    def test_context_no_state(self) -> None:
        ctx = ToolUseContext()
        assert ctx.get_app_state() is None


class TestToolResult:
    def test_basic_result(self) -> None:
        result = ToolResult(data="output")
        assert result.data == "output"
        assert result.new_messages is None
        assert result.context_modifier is None

    def test_result_with_messages(self) -> None:
        from claude_code.types.message import create_system_message

        msg = create_system_message("side effect")
        result = ToolResult(data="ok", new_messages=[msg])
        assert len(result.new_messages) == 1


class TestValidationResult:
    def test_valid(self) -> None:
        v = ValidationResult(result=True)
        assert v.result is True

    def test_invalid(self) -> None:
        v = ValidationResult(result=False, message="Bad input", error_code=400)
        assert v.result is False
        assert v.message == "Bad input"
