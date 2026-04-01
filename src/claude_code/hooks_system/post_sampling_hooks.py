"""Post-sampling hooks (run after each model turn)."""

from __future__ import annotations

from typing import Any

from claude_code.hooks_system.hook_runner import run_hooks_for_event
from claude_code.types.hooks import HookEvent, HookInput, HookResult


async def run_stop_hooks(
    hooks_config: dict[str, Any],
    *,
    session_id: str | None = None,
    cwd: str | None = None,
) -> list[HookResult]:
    """Run Stop hooks when the conversation ends."""
    hook_input = HookInput(
        hook_event=HookEvent.STOP,
        session_id=session_id,
        cwd=cwd,
    )
    return await run_hooks_for_event(HookEvent.STOP, hooks_config, hook_input)
