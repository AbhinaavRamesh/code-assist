"""Automatic compaction when context exceeds budget."""

from __future__ import annotations

import logging
from typing import Any

from claude_code.services.compact.compact import compact_messages
from claude_code.types.message import Message
from claude_code.utils.context import should_compact
from claude_code.utils.tokens import estimate_message_tokens

logger = logging.getLogger(__name__)


def maybe_auto_compact(
    messages: list[Message],
    model: str,
) -> tuple[list[Message], dict[str, Any] | None]:
    """Compact messages if context budget is exceeded.

    Returns (messages, metadata) where metadata is None if no compaction happened.
    """
    # Estimate current token usage
    api_messages = [
        {"content": getattr(m, "content", "")} for m in messages
    ]
    estimated_tokens = estimate_message_tokens(api_messages)

    if not should_compact(model, used_tokens=estimated_tokens):
        return messages, None

    logger.info(
        "Auto-compacting: ~%d tokens exceeds budget for %s",
        estimated_tokens,
        model,
    )

    new_messages, metadata = compact_messages(messages)
    metadata["trigger"] = "auto"
    metadata["pre_tokens"] = estimated_tokens
    return new_messages, metadata
