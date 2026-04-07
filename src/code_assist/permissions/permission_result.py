"""Permission result construction and query helpers."""

from __future__ import annotations

from typing import Any

from code_assist.types.permissions import (
    PermissionAllowDecision,
    PermissionAskDecision,
    PermissionDenyDecision,
    PermissionDecisionReason,
    PermissionResult,
    PermissionUpdate,
)


def create_allow_result(
    updated_input: dict[str, Any] | None = None,
    reason: PermissionDecisionReason | None = None,
) -> PermissionAllowDecision:
    """Create an allow decision."""
    return PermissionAllowDecision(
        updated_input=updated_input,
        decision_reason=reason,
    )


def create_deny_result(
    message: str,
    reason: PermissionDecisionReason | None = None,
) -> PermissionDenyDecision:
    """Create a deny decision with an explanation message."""
    return PermissionDenyDecision(
        message=message,
        decision_reason=reason,
    )


def create_ask_result(
    message: str,
    suggestions: list[PermissionUpdate] | None = None,
) -> PermissionAskDecision:
    """Create an ask decision requesting user confirmation."""
    return PermissionAskDecision(
        message=message,
        suggestions=suggestions,
    )


def is_allowed(result: PermissionResult) -> bool:
    """Return True if the result is an allow decision."""
    return result.behavior == "allow"


def is_denied(result: PermissionResult) -> bool:
    """Return True if the result is a deny decision."""
    return result.behavior == "deny"
