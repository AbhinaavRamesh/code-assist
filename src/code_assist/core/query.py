"""Main agent loop - the core query execution.

This is the heart of the system: sends messages to the API,
streams responses, dispatches tool calls, and loops until done.
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any

import anthropic

from code_assist.core.streaming import StreamAccumulator
from code_assist.services.api.claude import (
    SystemPrompt,
    build_system_prompt_param,
    create_anthropic_client,
    extract_usage,
    stream_message,
    tool_to_api_schema,
    APIClientConfig,
)
from code_assist.services.api.errors import classify_api_error
from code_assist.services.tools.tool_execution import ToolExecutionResult, execute_tool_use
from code_assist.tools.base import ToolDef, ToolUseContext, Tools
from code_assist.types.message import (
    AssistantMessage,
    Message,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    Usage,
    create_assistant_message,
    create_user_message,
)
from code_assist.utils.cost_tracker import track_usage

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Query Events (yielded to consumers)
# ---------------------------------------------------------------------------


@dataclass
class QueryEvent:
    """Base event yielded during query execution."""

    type: str = ""


@dataclass
class TextEvent(QueryEvent):
    """Text content from the assistant."""

    type: str = "text"
    text: str = ""


@dataclass
class ToolUseEvent(QueryEvent):
    """Tool use initiated by the assistant."""

    type: str = "tool_use"
    tool_use_id: str = ""
    tool_name: str = ""
    tool_input: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResultEvent(QueryEvent):
    """Result of a tool execution."""

    type: str = "tool_result"
    tool_use_id: str = ""
    result: str = ""
    is_error: bool = False


@dataclass
class AssistantMessageEvent(QueryEvent):
    """Complete assistant message."""

    type: str = "assistant_message"
    message: AssistantMessage = field(default_factory=AssistantMessage)


@dataclass
class ErrorEvent(QueryEvent):
    """An error occurred."""

    type: str = "error"
    error: str = ""
    is_retryable: bool = False


@dataclass
class DoneEvent(QueryEvent):
    """Query is complete."""

    type: str = "done"
    stop_reason: str = ""
    total_turns: int = 0
    total_cost_usd: float = 0.0


# ---------------------------------------------------------------------------
# Query Configuration
# ---------------------------------------------------------------------------


@dataclass
class QueryConfig:
    """Configuration for a query execution."""

    model: str = "claude-sonnet-4-6"
    max_tokens: int = 16384
    max_turns: int = 100
    system_prompt: SystemPrompt = field(default_factory=list)
    tools: Tools = field(default_factory=list)
    api_key: str | None = None
    base_url: str | None = None
    betas: list[str] | None = None
    stop_sequences: list[str] | None = None
    thinking: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Message Conversion
# ---------------------------------------------------------------------------


def _messages_to_api_format(messages: list[Message]) -> list[dict[str, Any]]:
    """Convert internal messages to Anthropic API format."""
    result: list[dict[str, Any]] = []

    for msg in messages:
        if hasattr(msg, "type"):
            if msg.type == "user":
                content = msg.content  # type: ignore[union-attr]
                if isinstance(content, str):
                    result.append({"role": "user", "content": content})
                elif isinstance(content, list):
                    blocks: list[dict[str, Any]] = []
                    for block in content:
                        if isinstance(block, TextBlock):
                            blocks.append({"type": "text", "text": block.text})
                        elif isinstance(block, ToolResultBlock):
                            blocks.append({
                                "type": "tool_result",
                                "tool_use_id": block.tool_use_id,
                                "content": block.content,
                                "is_error": block.is_error,
                            })
                    if blocks:
                        result.append({"role": "user", "content": blocks})

            elif msg.type == "assistant":
                blocks = []
                for block in msg.content:  # type: ignore[union-attr]
                    if isinstance(block, TextBlock):
                        blocks.append({"type": "text", "text": block.text})
                    elif isinstance(block, ToolUseBlock):
                        blocks.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        })
                if blocks:
                    result.append({"role": "assistant", "content": blocks})

    return result


def _tools_to_api_format(tools: Tools) -> list[dict[str, Any]]:
    """Convert tools to API tool schema format."""
    result: list[dict[str, Any]] = []
    for tool in tools:
        if not tool.is_enabled():
            continue
        schema = tool.input_schema.model_json_schema() if hasattr(tool.input_schema, "model_json_schema") else {"type": "object"}
        result.append(
            tool_to_api_schema(
                tool.name,
                "",  # Description generated at prompt level
                schema,
            )
        )
    return result


# ---------------------------------------------------------------------------
# Main Query Loop
# ---------------------------------------------------------------------------


async def query(
    messages: list[Message],
    config: QueryConfig,
    context: ToolUseContext,
) -> AsyncGenerator[QueryEvent, None]:
    """Execute the main agent loop.

    This is the core of the system:
    1. Send messages to the API
    2. Stream the response
    3. If tool_use blocks are present, execute them
    4. Append tool results and loop
    5. When stop_reason is 'end_turn', we're done
    """
    client_config = APIClientConfig(
        api_key=config.api_key,
        base_url=config.base_url,
        model=config.model,
        max_tokens=config.max_tokens,
    )
    client = create_anthropic_client(client_config)

    system_param = build_system_prompt_param(config.system_prompt) if config.system_prompt else None
    tools_param = _tools_to_api_format(config.tools) if config.tools else None

    turn = 0
    working_messages = list(messages)

    while turn < config.max_turns:
        turn += 1
        api_messages = _messages_to_api_format(working_messages)

        # Stream API response
        accumulator = StreamAccumulator()
        start_time = time.monotonic()

        try:
            async for event in stream_message(
                client,
                model=config.model,
                messages=api_messages,
                system=system_param,
                tools=tools_param,
                max_tokens=config.max_tokens,
                betas=config.betas,
                thinking=config.thinking,
                stop_sequences=config.stop_sequences,
            ):
                accumulator.handle_event(event)

                # Yield text as it streams
                delta = getattr(event, "delta", None)
                if delta and getattr(delta, "type", "") == "text_delta":
                    yield TextEvent(text=getattr(delta, "text", ""))

        except Exception as e:
            classified = classify_api_error(e)
            yield ErrorEvent(error=classified.message, is_retryable=classified.is_retryable)
            if not classified.is_retryable:
                return
            continue

        # Build assistant message
        assistant_msg = accumulator.to_message()
        duration_ms = (time.monotonic() - start_time) * 1000

        # Track usage
        if assistant_msg.usage:
            track_usage(config.model, assistant_msg.usage)

        working_messages.append(assistant_msg)
        yield AssistantMessageEvent(message=assistant_msg)

        # Check for tool use
        tool_uses = accumulator.get_tool_use_blocks()
        if not tool_uses or assistant_msg.stop_reason != "tool_use":
            yield DoneEvent(
                stop_reason=assistant_msg.stop_reason or "end_turn",
                total_turns=turn,
            )
            return

        # Execute tools and build tool results
        tool_result_blocks: list[ToolResultBlock] = []
        for tu in tool_uses:
            yield ToolUseEvent(
                tool_use_id=tu.id,
                tool_name=tu.name,
                tool_input=tu.input,
            )

            result = await execute_tool_use(
                tu.id,
                tu.name,
                tu.input,
                context=context,
                can_use_tool=lambda *a, **kw: None,
                parent_message=assistant_msg,
            )

            result_text = ""
            is_error = False
            if result.error:
                result_text = result.error
                is_error = True
            elif result.result:
                result_text = str(result.result.data) if result.result.data is not None else ""

            tool_result_blocks.append(
                ToolResultBlock(
                    tool_use_id=tu.id,
                    content=result_text,
                    is_error=is_error,
                )
            )
            yield ToolResultEvent(
                tool_use_id=tu.id,
                result=result_text,
                is_error=is_error,
            )

        # Append tool results as user message
        working_messages.append(
            create_user_message(tool_result_blocks)  # type: ignore[arg-type]
        )

    # Max turns reached
    yield DoneEvent(stop_reason="max_turns", total_turns=turn)
