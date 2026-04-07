"""Session start hooks."""

from __future__ import annotations

from typing import Any

from code_assist.hooks_system.hook_runner import run_hooks_for_event
from code_assist.types.hooks import HookEvent, HookInput, HookResult


async def run_session_start_hooks(
    hooks_config: dict[str, Any],
    *,
    session_id: str | None = None,
    cwd: str | None = None,
) -> list[HookResult]:
    """Run SessionStart hooks at the beginning of a session."""
    hook_input = HookInput(
        hook_event=HookEvent.SESSION_START,
        session_id=session_id,
        cwd=cwd,
    )
    return await run_hooks_for_event(HookEvent.SESSION_START, hooks_config, hook_input)
