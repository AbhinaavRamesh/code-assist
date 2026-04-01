"""Permission mode utilities.

Provides helpers for checking and querying permission modes.
"""

from __future__ import annotations

from claude_code.types.permissions import PermissionMode


def is_bypass_mode(mode: PermissionMode) -> bool:
    """Return True if the mode bypasses all permission checks."""
    return mode == PermissionMode.BYPASS_PERMISSIONS


def is_plan_mode(mode: PermissionMode) -> bool:
    """Return True if the mode is plan-only (no writes)."""
    return mode == PermissionMode.PLAN


def is_auto_mode(mode: PermissionMode) -> bool:
    """Return True if the mode auto-accepts most tool use."""
    return mode in (PermissionMode.AUTO, PermissionMode.DONT_ASK)


def allows_writes(mode: PermissionMode) -> bool:
    """Return True if the mode permits write operations.

    All modes allow writes except plan mode.
    """
    return mode != PermissionMode.PLAN


def allows_tool(mode: PermissionMode, tool_name: str) -> bool:
    """Return True if the mode allows a given tool to execute.

    In bypass mode every tool is allowed.
    In plan mode only read-only tools are permitted.
    In other modes the tool is provisionally allowed (further rule checks apply).
    """
    if is_bypass_mode(mode):
        return True

    if is_plan_mode(mode):
        read_only_tools = frozenset({
            "Read",
            "Glob",
            "Grep",
            "WebSearch",
            "WebFetch",
            "TodoRead",
            "ToolSearch",
        })
        return tool_name in read_only_tools

    # Default / auto / accept-edits -- provisionally allowed
    return True
