"""Retry logic with exponential backoff.

Retry logic with exponential backoff.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from code_assist.services.api.errors import classify_api_error

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def with_retry(
    fn: Callable[[], Awaitable[T]],
    *,
    max_retries: int = 3,
    base_delay_ms: int = 1000,
    max_delay_ms: int = 30000,
    on_retry: Callable[[int, Exception, int], Awaitable[None]] | None = None,
) -> T:
    """Execute an async function with exponential backoff retry.

    Args:
        fn: Async function to execute
        max_retries: Maximum number of retry attempts
        base_delay_ms: Base delay in milliseconds
        max_delay_ms: Maximum delay in milliseconds
        on_retry: Optional callback(attempt, error, delay_ms) called before each retry
    """
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except Exception as e:
            last_error = e
            classified = classify_api_error(e)

            if not classified.is_retryable or attempt >= max_retries:
                raise

            # Calculate delay with exponential backoff
            delay_ms = min(
                base_delay_ms * (2**attempt),
                max_delay_ms,
            )

            # Use retry-after header if available
            if classified.retry_after_ms is not None:
                delay_ms = max(delay_ms, classified.retry_after_ms)

            logger.warning(
                "API error (attempt %d/%d): %s. Retrying in %dms...",
                attempt + 1,
                max_retries,
                classified.message,
                delay_ms,
            )

            if on_retry:
                await on_retry(attempt, e, delay_ms)

            await asyncio.sleep(delay_ms / 1000)

    # Should not reach here, but satisfy type checker
    assert last_error is not None
    raise last_error
