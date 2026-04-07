"""Tests for the query engine core components."""

from __future__ import annotations

import pytest

from code_assist.core.process_input import ProcessedInput, process_user_input
from code_assist.core.query import (
    AssistantMessageEvent,
    DoneEvent,
    ErrorEvent,
    QueryConfig,
    TextEvent,
    ToolResultEvent,
    ToolUseEvent,
    _messages_to_api_format,
)
from code_assist.core.query_engine import QueryEngine, QueryEngineConfig
from code_assist.core.streaming import StreamAccumulator
from code_assist.types.message import (
    AssistantMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    Usage,
    UserMessage,
    create_assistant_message,
    create_user_message,
)
from code_assist.utils.messages import (
    count_tool_uses,
    get_last_text_block,
    get_text_content,
    is_tool_use_message,
)


# ---------------------------------------------------------------------------
# ProcessInput Tests
# ---------------------------------------------------------------------------


class TestProcessInput:
    def test_plain_text(self) -> None:
        result = process_user_input("hello world")
        assert not result.is_command
        assert result.prompt_text == "hello world"

    def test_slash_command(self) -> None:
        result = process_user_input("/help")
        assert result.is_command
        assert result.command_name == "help"
        assert result.command_args == ""

    def test_slash_command_with_args(self) -> None:
        result = process_user_input("/model sonnet")
        assert result.is_command
        assert result.command_name == "model"
        assert result.command_args == "sonnet"

    def test_shell_escape(self) -> None:
        result = process_user_input("! ls -la")
        assert result.is_command
        assert result.command_name == "!"
        assert result.command_args == "ls -la"

    def test_whitespace_stripped(self) -> None:
        result = process_user_input("  hello  ")
        assert result.prompt_text == "hello"


# ---------------------------------------------------------------------------
# StreamAccumulator Tests
# ---------------------------------------------------------------------------


class _MockEvent:
    """Helper to create mock stream events."""

    def __init__(self, **kwargs: object) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestStreamAccumulator:
    def test_message_start(self) -> None:
        acc = StreamAccumulator()
        msg = _MockEvent(id="msg_123", model="claude-sonnet-4-6", usage=_MockEvent(input_tokens=50))
        acc.handle_event(_MockEvent(type="message_start", message=msg))
        assert acc.message_id == "msg_123"
        assert acc.model == "claude-sonnet-4-6"

    def test_text_block(self) -> None:
        acc = StreamAccumulator()
        acc.handle_event(_MockEvent(
            type="content_block_start",
            index=0,
            content_block=_MockEvent(type="text"),
        ))
        acc.handle_event(_MockEvent(
            type="content_block_delta",
            delta=_MockEvent(type="text_delta", text="Hello "),
        ))
        acc.handle_event(_MockEvent(
            type="content_block_delta",
            delta=_MockEvent(type="text_delta", text="world"),
        ))
        acc.handle_event(_MockEvent(type="content_block_stop"))
        assert acc.get_text() == "Hello world"

    def test_tool_use_block(self) -> None:
        acc = StreamAccumulator()
        acc.handle_event(_MockEvent(
            type="content_block_start",
            index=0,
            content_block=_MockEvent(type="tool_use", id="tu_1", name="bash"),
        ))
        acc.handle_event(_MockEvent(
            type="content_block_delta",
            delta=_MockEvent(type="input_json_delta", partial_json='{"command":'),
        ))
        acc.handle_event(_MockEvent(
            type="content_block_delta",
            delta=_MockEvent(type="input_json_delta", partial_json=' "ls"}'),
        ))
        acc.handle_event(_MockEvent(type="content_block_stop"))

        tools = acc.get_tool_use_blocks()
        assert len(tools) == 1
        assert tools[0].name == "bash"
        assert tools[0].input == {"command": "ls"}

    def test_to_message(self) -> None:
        acc = StreamAccumulator()
        acc.message_id = "msg_1"
        acc.model = "claude-sonnet-4-6"
        acc.content_blocks = [TextBlock(text="hi")]
        acc.stop_reason = "end_turn"
        msg = acc.to_message()
        assert msg.type == "assistant"
        assert msg.stop_reason == "end_turn"

    def test_message_delta_stop_reason(self) -> None:
        acc = StreamAccumulator()
        acc.handle_event(_MockEvent(
            type="message_delta",
            delta=_MockEvent(stop_reason="end_turn"),
            usage=_MockEvent(output_tokens=100),
        ))
        assert acc.stop_reason == "end_turn"
        assert acc.usage.output_tokens == 100


# ---------------------------------------------------------------------------
# Message Conversion Tests
# ---------------------------------------------------------------------------


class TestMessageConversion:
    def test_user_text_message(self) -> None:
        msgs = [create_user_message("hello")]
        api = _messages_to_api_format(msgs)
        assert len(api) == 1
        assert api[0]["role"] == "user"
        assert api[0]["content"] == "hello"

    def test_assistant_message(self) -> None:
        msg = create_assistant_message([TextBlock(text="hi")])
        api = _messages_to_api_format([msg])
        assert len(api) == 1
        assert api[0]["role"] == "assistant"
        assert api[0]["content"][0]["type"] == "text"

    def test_tool_use_in_assistant(self) -> None:
        msg = create_assistant_message([
            ToolUseBlock(id="tu_1", name="bash", input={"command": "ls"}),
        ])
        api = _messages_to_api_format([msg])
        assert api[0]["content"][0]["type"] == "tool_use"
        assert api[0]["content"][0]["name"] == "bash"


# ---------------------------------------------------------------------------
# Query Event Tests
# ---------------------------------------------------------------------------


class TestQueryEvents:
    def test_text_event(self) -> None:
        e = TextEvent(text="hello")
        assert e.type == "text"

    def test_tool_use_event(self) -> None:
        e = ToolUseEvent(tool_use_id="tu_1", tool_name="bash")
        assert e.type == "tool_use"

    def test_done_event(self) -> None:
        e = DoneEvent(stop_reason="end_turn", total_turns=5)
        assert e.total_turns == 5


# ---------------------------------------------------------------------------
# QueryEngine Config Tests
# ---------------------------------------------------------------------------


class TestQueryEngineConfig:
    def test_default_config(self) -> None:
        config = QueryEngineConfig()
        assert config.model == "claude-sonnet-4-6"
        assert config.max_turns == 100

    def test_engine_creation(self) -> None:
        engine = QueryEngine(QueryEngineConfig(model="opus"))
        assert engine.messages == []
        assert engine.total_turns == 0

    def test_clear_messages(self) -> None:
        engine = QueryEngine(QueryEngineConfig())
        engine._messages.append(create_user_message("test"))
        assert len(engine.messages) == 1
        engine.clear_messages()
        assert len(engine.messages) == 0


# ---------------------------------------------------------------------------
# Message Utility Tests
# ---------------------------------------------------------------------------


class TestMessageUtils:
    def test_get_text_from_user(self) -> None:
        msg = create_user_message("hello")
        assert get_text_content(msg) == "hello"

    def test_get_text_from_assistant(self) -> None:
        msg = create_assistant_message([TextBlock(text="world")])
        assert get_text_content(msg) == "world"

    def test_count_tool_uses(self) -> None:
        msg = create_assistant_message([
            TextBlock(text="hi"),
            ToolUseBlock(id="1", name="bash"),
            ToolUseBlock(id="2", name="read"),
        ])
        assert count_tool_uses(msg) == 2

    def test_is_tool_use_message(self) -> None:
        msg1 = create_assistant_message([TextBlock(text="hi")])
        assert not is_tool_use_message(msg1)

        msg2 = create_assistant_message([ToolUseBlock(id="1", name="bash")])
        assert is_tool_use_message(msg2)

    def test_get_last_text_block(self) -> None:
        msg = create_assistant_message([
            TextBlock(text="first"),
            ToolUseBlock(id="1", name="bash"),
            TextBlock(text="last"),
        ])
        assert get_last_text_block(msg) == "last"

    def test_get_last_text_block_empty(self) -> None:
        msg = create_assistant_message([ToolUseBlock(id="1", name="bash")])
        assert get_last_text_block(msg) == ""
