"""API request/response logging and usage tracking."""

from __future__ import annotations

import logging
from typing import Any

from claude_code.types.message import Usage

logger = logging.getLogger(__name__)


def log_api_request(
    model: str,
    *,
    message_count: int = 0,
    tool_count: int = 0,
    system_prompt_length: int = 0,
) -> None:
    """Log an outgoing API request."""
    logger.debug(
        "API request: model=%s messages=%d tools=%d system_len=%d",
        model,
        message_count,
        tool_count,
        system_prompt_length,
    )


def log_api_response(
    model: str,
    usage: Usage,
    *,
    stop_reason: str | None = None,
    duration_ms: float = 0,
) -> None:
    """Log an API response."""
    logger.debug(
        "API response: model=%s in=%d out=%d cache_read=%d cache_create=%d "
        "stop=%s duration=%.0fms",
        model,
        usage.input_tokens,
        usage.output_tokens,
        usage.cache_read_input_tokens,
        usage.cache_creation_input_tokens,
        stop_reason,
        duration_ms,
    )
