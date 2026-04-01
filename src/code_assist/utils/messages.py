"""Message utility functions."""

from __future__ import annotations

from typing import Any

from code_assist.types.message import (
    AssistantMessage,
    Message,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)


def get_text_content(message: Message) -> str:
    """Extract text content from a message."""
    if isinstance(message, UserMessage):
        if isinstance(message.content, str):
            return message.content
        return " ".join(
            b.text for b in message.content if isinstance(b, TextBlock)
        )
    if isinstance(message, AssistantMessage):
        return " ".join(
            b.text for b in message.content if isinstance(b, TextBlock)
        )
    if isinstance(message, SystemMessage):
        return message.content
    return ""


def count_tool_uses(message: AssistantMessage) -> int:
    """Count tool_use blocks in an assistant message."""
    return sum(1 for b in message.content if isinstance(b, ToolUseBlock))


def get_last_text_block(message: AssistantMessage) -> str:
    """Get the last text block from an assistant message."""
    for block in reversed(message.content):
        if isinstance(block, TextBlock):
            return block.text
    return ""


def is_tool_use_message(message: AssistantMessage) -> bool:
    """Check if an assistant message contains tool uses."""
    return any(isinstance(b, ToolUseBlock) for b in message.content)
