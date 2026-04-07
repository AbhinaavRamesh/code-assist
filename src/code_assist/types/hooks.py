"""Hook system types.

Hook system types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal

from code_assist.types.permissions import PermissionResult, PermissionUpdate


# ---------------------------------------------------------------------------
# Hook Events
# ---------------------------------------------------------------------------


class HookEvent(StrEnum):
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    SESSION_START = "SessionStart"
    STOP = "Stop"
    NOTIFICATION = "Notification"
    SUBAGENT_START = "SubagentStart"
    POST_TOOL_USE_FAILURE = "PostToolUseFailure"
    PERMISSION_DENIED = "PermissionDenied"
    PERMISSION_REQUEST = "PermissionRequest"
    ELICITATION = "Elicitation"
    ELICITATION_RESULT = "ElicitationResult"
    FILE_CHANGED = "FileChanged"
    CWD_CHANGED = "CwdChanged"
    PRE_COMPACT = "PreCompact"
    POST_COMPACT = "PostCompact"


# ---------------------------------------------------------------------------
# Prompt Elicitation Protocol
# ---------------------------------------------------------------------------


@dataclass
class PromptOption:
    key: str = ""
    label: str = ""
    description: str | None = None


@dataclass
class PromptRequest:
    prompt: str = ""  # request id
    message: str = ""
    options: list[PromptOption] = field(default_factory=list)


@dataclass
class PromptResponse:
    prompt_response: str = ""  # request id
    selected: str = ""


# ---------------------------------------------------------------------------
# Hook Input / Output
# ---------------------------------------------------------------------------


@dataclass
class HookInput:
    """Input passed to a hook shell command as JSON on stdin."""

    hook_event: HookEvent = HookEvent.PRE_TOOL_USE
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_use_id: str | None = None
    tool_output: str | None = None
    user_prompt: str | None = None
    session_id: str | None = None
    agent_id: str | None = None
    cwd: str | None = None


@dataclass
class HookJSONOutput:
    """JSON output from a hook shell command."""

    # PreToolUse hooks
    decision: Literal["approve", "deny", "block"] | None = None
    reason: str | None = None
    updated_input: dict[str, Any] | None = None

    # PostToolUse hooks
    suppress_output: bool | None = None
    updated_output: str | None = None

    # UserPromptSubmit hooks
    updated_prompt: str | None = None

    # Permission updates
    permission_updates: list[dict[str, Any]] | None = None

    # Status message for progress
    status_message: str | None = None

    # Additional context to inject
    additional_context: str | None = None

    # Control flow
    prevent_continuation: bool | None = None
    stop_reason: str | None = None
    retry: bool | None = None


# ---------------------------------------------------------------------------
# Hook Progress
# ---------------------------------------------------------------------------


@dataclass
class HookProgress:
    type: Literal["hook_progress"] = "hook_progress"
    hook_event: HookEvent = HookEvent.PRE_TOOL_USE
    hook_name: str = ""
    command: str = ""
    prompt_text: str | None = None
    status_message: str | None = None


@dataclass
class HookBlockingError:
    blocking_error: str = ""
    command: str = ""


# ---------------------------------------------------------------------------
# Hook Results
# ---------------------------------------------------------------------------


@dataclass
class PermissionRequestAllowResult:
    behavior: Literal["allow"] = "allow"
    updated_input: dict[str, Any] | None = None
    updated_permissions: list[PermissionUpdate] | None = None


@dataclass
class PermissionRequestDenyResult:
    behavior: Literal["deny"] = "deny"
    message: str | None = None
    interrupt: bool | None = None


PermissionRequestResult = PermissionRequestAllowResult | PermissionRequestDenyResult


class HookOutcome(StrEnum):
    SUCCESS = "success"
    BLOCKING = "blocking"
    NON_BLOCKING_ERROR = "non_blocking_error"
    CANCELLED = "cancelled"


@dataclass
class HookResult:
    """Result from executing a single hook."""

    outcome: HookOutcome = HookOutcome.SUCCESS
    message: Any = None  # Message type (circular import avoidance)
    system_message: Any = None
    blocking_error: HookBlockingError | None = None
    prevent_continuation: bool | None = None
    stop_reason: str | None = None
    permission_behavior: Literal["ask", "deny", "allow", "passthrough"] | None = None
    hook_permission_decision_reason: str | None = None
    additional_context: str | None = None
    initial_user_message: str | None = None
    updated_input: dict[str, Any] | None = None
    updated_mcp_tool_output: Any = None
    permission_request_result: PermissionRequestResult | None = None
    retry: bool | None = None


@dataclass
class AggregatedHookResult:
    """Aggregated result from executing multiple hooks."""

    message: Any = None
    blocking_errors: list[HookBlockingError] | None = None
    prevent_continuation: bool | None = None
    stop_reason: str | None = None
    hook_permission_decision_reason: str | None = None
    permission_behavior: str | None = None
    additional_contexts: list[str] | None = None
    initial_user_message: str | None = None
    updated_input: dict[str, Any] | None = None
    updated_mcp_tool_output: Any = None
    permission_request_result: PermissionRequestResult | None = None
    retry: bool | None = None
