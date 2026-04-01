"""Core conversation compaction - summarize and replace old messages."""

from __future__ import annotations

import logging
from typing import Any

from claude_code.types.message import (
    AssistantMessage,
    Message,
    SystemMessage,
    SystemMessageSubtype,
    TextBlock,
    UserMessage,
    create_assistant_message,
    create_system_message,
    create_user_message,
)
from claude_code.utils.messages import get_text_content
from claude_code.utils.tokens import rough_token_estimate

logger = logging.getLogger(__name__)


def build_compaction_summary(messages: list[Message]) -> str:
    """Build a summary of messages for compaction."""
    parts: list[str] = []
    for msg in messages:
        text = get_text_content(msg)
        if text:
            role = getattr(msg, "type", "unknown")
            # Truncate long messages
            if len(text) > 500:
                text = text[:500] + "..."
            parts.append(f"[{role}] {text}")
    return "\n".join(parts)


def compact_messages(
    messages: list[Message],
    *,
    preserve_last_n: int = 4,
    max_summary_tokens: int = 2000,
) -> tuple[list[Message], dict[str, Any]]:
    """Compact a conversation by summarizing old messages.

    Preserves the last N messages and summarizes everything before them.

    Returns:
        Tuple of (new_messages, compaction_metadata)
    """
    if len(messages) <= preserve_last_n:
        return messages, {"compacted": False}

    # Split into old and recent
    old_messages = messages[:-preserve_last_n]
    recent_messages = messages[-preserve_last_n:]

    # Build summary of old messages
    summary = build_compaction_summary(old_messages)

    # Truncate summary if too long
    estimated_tokens = rough_token_estimate(summary)
    if estimated_tokens > max_summary_tokens:
        ratio = max_summary_tokens / estimated_tokens
        summary = summary[: int(len(summary) * ratio)] + "\n[...truncated]"

    # Create summary message
    summary_msg = create_system_message(
        f"[Conversation compacted. Summary of prior messages:]\n\n{summary}",
        subtype=SystemMessageSubtype.COMPACT_BOUNDARY,
    )

    new_messages = [summary_msg, *recent_messages]

    metadata = {
        "compacted": True,
        "messages_removed": len(old_messages),
        "messages_preserved": len(recent_messages),
        "summary_length": len(summary),
        "trigger": "manual",
    }

    return new_messages, metadata
