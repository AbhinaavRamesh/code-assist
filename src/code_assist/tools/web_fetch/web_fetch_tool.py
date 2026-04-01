"""WebFetch tool - fetch and extract content from URLs.

Uses httpx to fetch web pages and extracts text content.
"""

from __future__ import annotations

import re
from typing import Any

import httpx
from pydantic import BaseModel, Field

from code_assist.tools.base import (
    CanUseToolFn,
    SearchOrReadInfo,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
)
from code_assist.types.message import AssistantMessage

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_CONTENT_SIZE = 50_000  # chars
REQUEST_TIMEOUT = 30.0  # seconds


# ---------------------------------------------------------------------------
# Input Schema
# ---------------------------------------------------------------------------


class WebFetchInput(BaseModel):
    """Input for the WebFetch tool."""

    url: str = Field(description="URL to fetch")
    prompt: str | None = Field(
        default=None,
        description="What to extract from the page content.",
    )


# ---------------------------------------------------------------------------
# Tool Implementation
# ---------------------------------------------------------------------------


class WebFetchTool(ToolDef):
    """Fetch and extract content from URLs.

    Uses httpx to fetch web pages, strips HTML tags to extract text content,
    and truncates to a maximum size.
    """

    name = "WebFetch"
    search_hint = "fetch url web page http download"
    max_result_size_chars = MAX_CONTENT_SIZE

    @property
    def input_schema(self) -> type[BaseModel]:
        return WebFetchInput

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        input_args: WebFetchInput = args  # type: ignore[assignment]

        url = input_args.url
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=REQUEST_TIMEOUT,
            ) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (compatible; CodeAssist/1.0; "
                            "+https://github.com/anthropics/claude-code)"
                        ),
                    },
                )
                response.raise_for_status()
        except httpx.TimeoutException:
            return ToolResult(data=f"Error: request to {url} timed out")
        except httpx.HTTPStatusError as exc:
            return ToolResult(
                data=f"Error: HTTP {exc.response.status_code} from {url}"
            )
        except httpx.HTTPError as exc:
            return ToolResult(data=f"Error fetching {url}: {exc}")

        content_type = response.headers.get("content-type", "")
        raw_text = response.text

        # Strip HTML if it looks like an HTML page
        if "html" in content_type.lower() or raw_text.strip().startswith("<"):
            text = _strip_html(raw_text)
        else:
            text = raw_text

        # Truncate
        if len(text) > MAX_CONTENT_SIZE:
            text = text[:MAX_CONTENT_SIZE] + "\n\n[Content truncated]"

        # Prepend prompt context if provided
        if input_args.prompt:
            text = f"Extraction prompt: {input_args.prompt}\n\n{text}"

        return ToolResult(data=text)

    async def description(self, input: BaseModel, options: Any) -> str:
        args: WebFetchInput = input  # type: ignore[assignment]
        return f"WebFetch: {args.url}"

    def is_read_only(self, input: BaseModel) -> bool:
        return True

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True

    def is_search_or_read_command(self, input: BaseModel) -> SearchOrReadInfo:
        return SearchOrReadInfo(is_read=True)


# ---------------------------------------------------------------------------
# HTML stripping
# ---------------------------------------------------------------------------

# Tags whose content should be removed entirely
_REMOVE_TAGS = re.compile(
    r"<(script|style|noscript|svg|iframe)[^>]*>.*?</\1>",
    re.DOTALL | re.IGNORECASE,
)

_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\n{3,}")


def _strip_html(html: str) -> str:
    """Remove HTML tags and return plain text."""
    text = _REMOVE_TAGS.sub("", html)
    text = _TAG_RE.sub("", text)
    # Collapse excessive blank lines
    text = _WHITESPACE_RE.sub("\n\n", text)
    return text.strip()
