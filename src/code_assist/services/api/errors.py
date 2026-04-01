"""API error classification and recovery.

Ports the TypeScript error handling from src/services/api/errors.ts.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from code_assist.utils.errors import (
    APIError,
    OverloadedError,
    PromptTooLongError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


class APIErrorType(StrEnum):
    AUTHENTICATION_FAILED = "authentication_failed"
    BILLING_ERROR = "billing_error"
    RATE_LIMIT = "rate_limit"
    INVALID_REQUEST = "invalid_request"
    SERVER_ERROR = "server_error"
    UNKNOWN = "unknown"
    MAX_OUTPUT_TOKENS = "max_output_tokens"
    PROMPT_TOO_LONG = "prompt_too_long"
    OVERLOADED = "overloaded"
    MEDIA_SIZE = "media_size"
    CONNECTION_ERROR = "connection_error"


@dataclass
class ClassifiedError:
    """Result of classifying an API error."""

    error_type: APIErrorType
    message: str
    status_code: int | None = None
    is_retryable: bool = False
    retry_after_ms: int | None = None
    prompt_token_count: int | None = None
    prompt_token_limit: int | None = None


def classify_api_error(error: Exception) -> ClassifiedError:
    """Classify an API error into a specific type.

    Maps Anthropic SDK errors to our internal error types.
    """
    import anthropic

    status_code = getattr(error, "status_code", None)
    message = str(error)

    # Authentication errors (401)
    if isinstance(error, anthropic.AuthenticationError):
        return ClassifiedError(
            error_type=APIErrorType.AUTHENTICATION_FAILED,
            message="Authentication failed. Check your API key.",
            status_code=401,
        )

    # Rate limit errors (429)
    if isinstance(error, anthropic.RateLimitError):
        retry_after = _extract_retry_after(error)
        return ClassifiedError(
            error_type=APIErrorType.RATE_LIMIT,
            message="Rate limit exceeded. Will retry.",
            status_code=429,
            is_retryable=True,
            retry_after_ms=retry_after,
        )

    # Overloaded (529)
    if status_code == 529 or isinstance(error, anthropic.APIStatusError) and getattr(error, "status_code", 0) == 529:
        return ClassifiedError(
            error_type=APIErrorType.OVERLOADED,
            message="API is overloaded. Will retry.",
            status_code=529,
            is_retryable=True,
            retry_after_ms=5000,
        )

    # Bad request (400) - check for specific subtypes
    if isinstance(error, anthropic.BadRequestError):
        return _classify_bad_request(error, message)

    # Server errors (500+)
    if isinstance(error, anthropic.InternalServerError):
        return ClassifiedError(
            error_type=APIErrorType.SERVER_ERROR,
            message="Server error. Will retry.",
            status_code=500,
            is_retryable=True,
        )

    # Connection errors
    if isinstance(error, anthropic.APIConnectionError):
        return ClassifiedError(
            error_type=APIErrorType.CONNECTION_ERROR,
            message=f"Connection error: {message}",
            is_retryable=True,
            retry_after_ms=2000,
        )

    # Unknown
    return ClassifiedError(
        error_type=APIErrorType.UNKNOWN,
        message=message,
        status_code=status_code,
    )


def _classify_bad_request(error: Exception, message: str) -> ClassifiedError:
    """Classify a 400 Bad Request error into subtypes."""
    lower = message.lower()

    # Prompt too long
    if "prompt is too long" in lower or "context length" in lower:
        tokens = _extract_token_counts(message)
        return ClassifiedError(
            error_type=APIErrorType.PROMPT_TOO_LONG,
            message="Prompt is too long. Will compact.",
            status_code=400,
            prompt_token_count=tokens[0],
            prompt_token_limit=tokens[1],
        )

    # Media size error
    if "image" in lower and ("size" in lower or "large" in lower):
        return ClassifiedError(
            error_type=APIErrorType.MEDIA_SIZE,
            message="Image or media too large.",
            status_code=400,
        )

    # Billing error
    if "billing" in lower or "payment" in lower:
        return ClassifiedError(
            error_type=APIErrorType.BILLING_ERROR,
            message="Billing error. Check your account.",
            status_code=400,
        )

    # Generic invalid request
    return ClassifiedError(
        error_type=APIErrorType.INVALID_REQUEST,
        message=message,
        status_code=400,
    )


def _extract_retry_after(error: Exception) -> int | None:
    """Extract retry-after time from error headers."""
    response = getattr(error, "response", None)
    if response is not None:
        headers = getattr(response, "headers", {})
        retry_after = headers.get("retry-after")
        if retry_after:
            try:
                return int(float(retry_after) * 1000)
            except ValueError:
                pass
    return None


def _extract_token_counts(message: str) -> tuple[int | None, int | None]:
    """Extract token count and limit from error message."""
    actual = None
    limit = None

    # Common patterns: "X tokens" and "limit of Y"
    actual_match = re.search(r"(\d[\d,]+)\s*tokens", message)
    limit_match = re.search(r"(?:limit|maximum|max)\s*(?:of\s*)?(\d[\d,]+)", message)

    if actual_match:
        actual = int(actual_match.group(1).replace(",", ""))
    if limit_match:
        limit = int(limit_match.group(1).replace(",", ""))

    return actual, limit


def error_to_exception(classified: ClassifiedError) -> APIError:
    """Convert a ClassifiedError to the appropriate exception type."""
    match classified.error_type:
        case APIErrorType.PROMPT_TOO_LONG:
            return PromptTooLongError(
                classified.message, status_code=classified.status_code
            )
        case APIErrorType.RATE_LIMIT:
            return RateLimitError(
                classified.message, status_code=classified.status_code
            )
        case APIErrorType.OVERLOADED:
            return OverloadedError(
                classified.message, status_code=classified.status_code
            )
        case _:
            return APIError(
                classified.message, status_code=classified.status_code
            )
