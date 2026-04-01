"""Tool execution hooks - pre/post tool use hook integration.

Connects tool execution to the hooks system.
"""

from __future__ import annotations

from typing import Any

from code_assist.types.hooks import HookEvent, HookInput, HookResult


async def run_pre_tool_use_hooks(
    tool_name: str,
    tool_input: dict[str, Any],
    tool_use_id: str,
    *,
    session_id: str | None = None,
    agent_id: str | None = None,
    cwd: str | None = None,
) -> HookResult | None:
    """Run PreToolUse hooks before tool execution.

    Returns None if no hooks are configured, or the aggregated result.
    Full implementation in Branch 14 (hooks).
    """
    return None


async def run_post_tool_use_hooks(
    tool_name: str,
    tool_input: dict[str, Any],
    tool_output: str,
    tool_use_id: str,
    *,
    session_id: str | None = None,
    agent_id: str | None = None,
    cwd: str | None = None,
) -> HookResult | None:
    """Run PostToolUse hooks after tool execution.

    Returns None if no hooks are configured.
    Full implementation in Branch 14 (hooks).
    """
    return None
