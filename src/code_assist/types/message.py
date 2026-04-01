"""Message types for the conversation system.

Message types for the conversation system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal


# ---------------------------------------------------------------------------
# Content Block Types (matching Anthropic API)
# ---------------------------------------------------------------------------


@dataclass
class TextBlock:
    type: Literal["text"] = "text"
    text: str = ""


@dataclass
class ToolUseBlock:
    type: Literal["tool_use"] = "tool_use"
    id: str = ""
    name: str = ""
    input: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResultBlock:
    type: Literal["tool_result"] = "tool_result"
    tool_use_id: str = ""
    content: str | list[TextBlock] = ""
    is_error: bool = False


@dataclass
class ThinkingBlock:
    type: Literal["thinking"] = "thinking"
    thinking: str = ""
    signature: str = ""


@dataclass
class RedactedThinkingBlock:
    type: Literal["redacted_thinking"] = "redacted_thinking"
    data: str = ""


@dataclass
class ImageBlock:
    type: Literal["image"] = "image"
    source: dict[str, Any] = field(default_factory=dict)


ContentBlock = (
    TextBlock
    | ToolUseBlock
    | ToolResultBlock
    | ThinkingBlock
    | RedactedThinkingBlock
    | ImageBlock
)


# ---------------------------------------------------------------------------
# Usage Tracking
# ---------------------------------------------------------------------------


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


@dataclass
class ModelUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    web_search_requests: int = 0
    cost_usd: float = 0.0
    context_window: int = 0
    max_output_tokens: int = 0


# ---------------------------------------------------------------------------
# Core Message Types (internal representation)
# ---------------------------------------------------------------------------


@dataclass
class UserMessage:
    """Message from the user."""

    type: Literal["user"] = "user"
    id: str = ""
    content: str | list[ContentBlock] = ""
    attachments: list[dict[str, Any]] = field(default_factory=list)
    is_synthetic: bool = False
    tool_use_result: Any = None
    priority: Literal["now", "next", "later"] | None = None
    timestamp: str | None = None


@dataclass
class AssistantMessage:
    """Response from Claude."""

    type: Literal["assistant"] = "assistant"
    id: str = ""
    content: list[ContentBlock] = field(default_factory=list)
    model: str = ""
    stop_reason: str | None = None
    stop_sequence: str | None = None
    usage: Usage = field(default_factory=Usage)
    is_api_error_message: bool = False
    error_details: str | None = None


class SystemMessageSubtype(StrEnum):
    INIT = "init"
    COMPACT_BOUNDARY = "compact_boundary"
    STATUS = "status"
    API_RETRY = "api_retry"
    LOCAL_COMMAND_OUTPUT = "local_command_output"
    HOOK_STARTED = "hook_started"
    HOOK_PROGRESS = "hook_progress"
    HOOK_RESPONSE = "hook_response"
    TASK_NOTIFICATION = "task_notification"
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    SESSION_STATE_CHANGED = "session_state_changed"
    FILES_PERSISTED = "files_persisted"
    POST_TURN_SUMMARY = "post_turn_summary"
    ELICITATION_COMPLETE = "elicitation_complete"


@dataclass
class SystemMessage:
    """System-generated message."""

    type: Literal["system"] = "system"
    id: str = ""
    subtype: SystemMessageSubtype = SystemMessageSubtype.STATUS
    content: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    is_local_command: bool = False


@dataclass
class ProgressMessage:
    """Tool progress update message."""

    type: Literal["progress"] = "progress"
    id: str = ""
    tool_use_id: str = ""
    tool_name: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    parent_tool_use_id: str | None = None
    elapsed_time_seconds: float = 0.0
    task_id: str | None = None


@dataclass
class TombstoneMessage:
    """Deleted/replaced message marker."""

    type: Literal["tombstone"] = "tombstone"
    id: str = ""
    original_type: str = ""


@dataclass
class AttachmentMessage:
    """Message with file attachments."""

    type: Literal["attachment"] = "attachment"
    id: str = ""
    content: list[ContentBlock] = field(default_factory=list)
    attachment_type: str = ""


# Union of all message types
Message = (
    UserMessage
    | AssistantMessage
    | SystemMessage
    | ProgressMessage
    | TombstoneMessage
    | AttachmentMessage
)


# ---------------------------------------------------------------------------
# SDK Message Types (external representation for structured I/O)
# ---------------------------------------------------------------------------


class SDKMessageType(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    RESULT = "result"
    SYSTEM = "system"
    STREAM_EVENT = "stream_event"
    TOOL_PROGRESS = "tool_progress"
    TOOL_USE_SUMMARY = "tool_use_summary"
    AUTH_STATUS = "auth_status"
    RATE_LIMIT_EVENT = "rate_limit_event"
    PROMPT_SUGGESTION = "prompt_suggestion"


class SDKResultSubtype(StrEnum):
    SUCCESS = "success"
    ERROR_DURING_EXECUTION = "error_during_execution"
    ERROR_MAX_TURNS = "error_max_turns"
    ERROR_MAX_BUDGET_USD = "error_max_budget_usd"
    ERROR_MAX_STRUCTURED_OUTPUT_RETRIES = "error_max_structured_output_retries"


class SDKErrorType(StrEnum):
    AUTHENTICATION_FAILED = "authentication_failed"
    BILLING_ERROR = "billing_error"
    RATE_LIMIT = "rate_limit"
    INVALID_REQUEST = "invalid_request"
    SERVER_ERROR = "server_error"
    UNKNOWN = "unknown"
    MAX_OUTPUT_TOKENS = "max_output_tokens"


class SessionState(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    REQUIRES_ACTION = "requires_action"


class FastModeState(StrEnum):
    OFF = "off"
    COOLDOWN = "cooldown"
    ON = "on"


@dataclass
class SDKPermissionDenial:
    tool_name: str = ""
    tool_use_id: str = ""
    tool_input: dict[str, Any] = field(default_factory=dict)


@dataclass
class SDKRateLimitInfo:
    status: Literal["allowed", "allowed_warning", "rejected"] = "allowed"
    resets_at: int | None = None
    rate_limit_type: str | None = None
    utilization: float | None = None
    overage_status: str | None = None
    overage_resets_at: int | None = None
    overage_disabled_reason: str | None = None
    is_using_overage: bool | None = None
    surpassed_threshold: float | None = None


# ---------------------------------------------------------------------------
# Message Factory Functions
# ---------------------------------------------------------------------------


_message_counter = 0


def _next_id(prefix: str = "msg") -> str:
    """Generate a unique message ID."""
    global _message_counter
    _message_counter += 1
    import uuid as _uuid

    return f"{prefix}_{_uuid.uuid4().hex[:12]}"


def create_user_message(
    content: str | list[ContentBlock],
    *,
    attachments: list[dict[str, Any]] | None = None,
    is_synthetic: bool = False,
    priority: Literal["now", "next", "later"] | None = None,
) -> UserMessage:
    """Create a new user message."""
    return UserMessage(
        id=_next_id("user"),
        content=content,
        attachments=attachments or [],
        is_synthetic=is_synthetic,
        priority=priority,
    )


def create_assistant_message(
    content: list[ContentBlock] | None = None,
    *,
    model: str = "",
    usage: Usage | None = None,
) -> AssistantMessage:
    """Create a new assistant message."""
    return AssistantMessage(
        id=_next_id("asst"),
        content=content or [],
        model=model,
        usage=usage or Usage(),
    )


def create_system_message(
    content: str,
    *,
    subtype: SystemMessageSubtype = SystemMessageSubtype.STATUS,
    data: dict[str, Any] | None = None,
) -> SystemMessage:
    """Create a new system message."""
    return SystemMessage(
        id=_next_id("sys"),
        subtype=subtype,
        content=content,
        data=data or {},
    )


def create_progress_message(
    tool_use_id: str,
    tool_name: str,
    data: dict[str, Any] | None = None,
    *,
    parent_tool_use_id: str | None = None,
) -> ProgressMessage:
    """Create a new progress message."""
    return ProgressMessage(
        id=_next_id("prog"),
        tool_use_id=tool_use_id,
        tool_name=tool_name,
        data=data or {},
        parent_tool_use_id=parent_tool_use_id,
    )


def create_api_error_message(
    error_text: str,
    *,
    error_type: SDKErrorType = SDKErrorType.UNKNOWN,
) -> AssistantMessage:
    """Create an assistant message representing an API error."""
    return AssistantMessage(
        id=_next_id("err"),
        content=[TextBlock(text=error_text)],
        is_api_error_message=True,
        error_details=error_type.value,
    )
