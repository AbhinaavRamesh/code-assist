"""Reactive compaction on prompt_too_long errors."""

from __future__ import annotations

import logging
from typing import Any

from code_assist.services.compact.compact import compact_messages
from code_assist.types.message import Message

logger = logging.getLogger(__name__)


def reactive_compact(
    messages: list[Message],
    *,
    token_count: int | None = None,
    token_limit: int | None = None,
) -> tuple[list[Message], dict[str, Any]]:
    """Compact messages in response to a prompt_too_long error.

    More aggressive than auto-compact - preserves fewer messages.
    """
    logger.warning(
        "Reactive compaction triggered (tokens: %s, limit: %s)",
        token_count,
        token_limit,
    )

    # Be more aggressive - preserve only last 2 messages
    new_messages, metadata = compact_messages(messages, preserve_last_n=2)
    metadata["trigger"] = "reactive"
    if token_count:
        metadata["pre_tokens"] = token_count
    if token_limit:
        metadata["token_limit"] = token_limit
    return new_messages, metadata
