"""Anthropic API client wrapper with streaming support.

Ports the TypeScript API client from src/services/api/claude.ts.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any

import anthropic

from code_assist.services.api.errors import classify_api_error
from code_assist.types.message import ModelUsage, Usage
from code_assist.utils.model.cost import calculate_cost_usd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Beta Headers
# ---------------------------------------------------------------------------

CONTEXT_1M_BETA_HEADER = "context-1m-2025-04-14"
PROMPT_CACHING_SCOPE_BETA_HEADER = "prompt-caching-scope-2025-06-01"
EFFORT_BETA_HEADER = "effort-2025-04-30"
FAST_MODE_BETA_HEADER = "fast-mode-2025-04-30"
STRUCTURED_OUTPUTS_BETA_HEADER = "structured-outputs-2025-04-30"
TOKEN_EFFICIENT_TOOLS_HEADER = "token-efficient-tool-inputs-2025-05-14"


def get_default_betas() -> list[str]:
    """Get the default beta headers to send with API requests."""
    return [
        CONTEXT_1M_BETA_HEADER,
        PROMPT_CACHING_SCOPE_BETA_HEADER,
        TOKEN_EFFICIENT_TOOLS_HEADER,
    ]


# ---------------------------------------------------------------------------
# System Prompt Types
# ---------------------------------------------------------------------------


@dataclass
class SystemPromptBlock:
    """A block of the system prompt with optional cache control."""

    type: str = "text"
    text: str = ""
    cache_control: dict[str, str] | None = None


SystemPrompt = list[SystemPromptBlock]


# ---------------------------------------------------------------------------
# Stream Event Types
# ---------------------------------------------------------------------------


@dataclass
class StreamEvent:
    """An event from the streaming API response."""

    type: str = ""
    index: int | None = None
    content_block: dict[str, Any] | None = None
    delta: dict[str, Any] | None = None
    message: dict[str, Any] | None = None
    usage: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# API Client
# ---------------------------------------------------------------------------


@dataclass
class APIClientConfig:
    """Configuration for the API client."""

    api_key: str | None = None
    base_url: str | None = None
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 16384
    betas: list[str] = field(default_factory=get_default_betas)
    timeout: float = 600.0
    max_retries: int = 2


def create_anthropic_client(config: APIClientConfig) -> anthropic.AsyncAnthropic:
    """Create an Anthropic async client."""
    kwargs: dict[str, Any] = {
        "timeout": config.timeout,
        "max_retries": config.max_retries,
    }
    if config.api_key:
        kwargs["api_key"] = config.api_key
    if config.base_url:
        kwargs["base_url"] = config.base_url
    return anthropic.AsyncAnthropic(**kwargs)


def build_system_prompt_param(
    system_prompt: SystemPrompt,
) -> list[dict[str, Any]]:
    """Convert SystemPrompt to API format."""
    result: list[dict[str, Any]] = []
    for block in system_prompt:
        entry: dict[str, Any] = {"type": block.type, "text": block.text}
        if block.cache_control:
            entry["cache_control"] = block.cache_control
        result.append(entry)
    return result


def tool_to_api_schema(
    name: str,
    description: str,
    input_schema: dict[str, Any],
    *,
    cache_control: dict[str, str] | None = None,
    strict: bool = False,
) -> dict[str, Any]:
    """Convert a tool definition to API tool schema format."""
    tool: dict[str, Any] = {
        "name": name,
        "description": description,
        "input_schema": input_schema,
    }
    if cache_control:
        tool["cache_control"] = cache_control
    if strict:
        tool["strict"] = True
    return tool


async def stream_message(
    client: anthropic.AsyncAnthropic,
    *,
    model: str,
    messages: list[dict[str, Any]],
    system: list[dict[str, Any]] | None = None,
    tools: list[dict[str, Any]] | None = None,
    max_tokens: int = 16384,
    betas: list[str] | None = None,
    thinking: dict[str, Any] | None = None,
    stop_sequences: list[str] | None = None,
) -> AsyncGenerator[Any, None]:
    """Stream a message from the Anthropic API.

    Yields raw stream events from the SDK.
    """
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if system:
        kwargs["system"] = system
    if tools:
        kwargs["tools"] = tools
    if stop_sequences:
        kwargs["stop_sequences"] = stop_sequences
    if thinking:
        kwargs["thinking"] = thinking

    extra_headers: dict[str, str] = {}
    if betas:
        kwargs["extra_headers"] = {
            "anthropic-beta": ",".join(betas),
            **extra_headers,
        }

    async with client.messages.stream(**kwargs) as stream:
        async for event in stream:
            yield event


# ---------------------------------------------------------------------------
# Usage Tracking
# ---------------------------------------------------------------------------


def extract_usage(response_usage: Any) -> Usage:
    """Extract usage data from an API response."""
    if response_usage is None:
        return Usage()
    return Usage(
        input_tokens=getattr(response_usage, "input_tokens", 0),
        output_tokens=getattr(response_usage, "output_tokens", 0),
        cache_read_input_tokens=getattr(response_usage, "cache_read_input_tokens", 0),
        cache_creation_input_tokens=getattr(
            response_usage, "cache_creation_input_tokens", 0
        ),
    )


def usage_to_model_usage(
    usage: Usage,
    model: str,
    *,
    context_window: int = 200_000,
    max_output_tokens: int = 16384,
) -> ModelUsage:
    """Convert Usage to ModelUsage with cost calculation."""
    cost = calculate_cost_usd(
        model,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_read_tokens=usage.cache_read_input_tokens,
        cache_creation_tokens=usage.cache_creation_input_tokens,
    )
    return ModelUsage(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_read_input_tokens=usage.cache_read_input_tokens,
        cache_creation_input_tokens=usage.cache_creation_input_tokens,
        cost_usd=cost,
        context_window=context_window,
        max_output_tokens=max_output_tokens,
    )
