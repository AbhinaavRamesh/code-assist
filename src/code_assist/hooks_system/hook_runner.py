"""Execute user-defined hooks (shell commands returning JSON)."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from code_assist.types.hooks import (
    HookBlockingError,
    HookEvent,
    HookInput,
    HookJSONOutput,
    HookOutcome,
    HookResult,
)

logger = logging.getLogger(__name__)


async def run_hook_command(
    command: str,
    hook_input: HookInput,
    *,
    timeout: float = 30.0,
) -> HookResult:
    """Execute a hook shell command and parse its JSON output.

    The hook receives JSON on stdin and returns JSON on stdout.
    """
    input_json = json.dumps({
        "hook_event": hook_input.hook_event,
        "tool_name": hook_input.tool_name,
        "tool_input": hook_input.tool_input,
        "tool_use_id": hook_input.tool_use_id,
        "session_id": hook_input.session_id,
        "cwd": hook_input.cwd,
    })

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input_json.encode()), timeout=timeout
        )

        if proc.returncode != 0:
            error_text = stderr.decode(errors="replace").strip()
            return HookResult(
                outcome=HookOutcome.NON_BLOCKING_ERROR,
                blocking_error=HookBlockingError(
                    blocking_error=error_text or f"Hook exited with code {proc.returncode}",
                    command=command,
                ),
            )

        # Parse JSON output
        output_text = stdout.decode(errors="replace").strip()
        if not output_text:
            return HookResult(outcome=HookOutcome.SUCCESS)

        try:
            output_data = json.loads(output_text)
        except json.JSONDecodeError:
            return HookResult(outcome=HookOutcome.SUCCESS)

        # Map JSON output to HookResult
        result = HookResult(outcome=HookOutcome.SUCCESS)

        decision = output_data.get("decision")
        if decision == "deny":
            result.permission_behavior = "deny"
            result.prevent_continuation = True
        elif decision == "block":
            result.outcome = HookOutcome.BLOCKING
            result.blocking_error = HookBlockingError(
                blocking_error=output_data.get("reason", "Blocked by hook"),
                command=command,
            )
        elif decision == "approve":
            result.permission_behavior = "allow"

        if "updated_input" in output_data:
            result.updated_input = output_data["updated_input"]
        if "additional_context" in output_data:
            result.additional_context = output_data["additional_context"]
        if "stop_reason" in output_data:
            result.stop_reason = output_data["stop_reason"]
            result.prevent_continuation = True

        return result

    except asyncio.TimeoutError:
        return HookResult(
            outcome=HookOutcome.NON_BLOCKING_ERROR,
            blocking_error=HookBlockingError(
                blocking_error=f"Hook timed out after {timeout}s",
                command=command,
            ),
        )
    except Exception as e:
        logger.warning("Hook execution failed: %s", e)
        return HookResult(
            outcome=HookOutcome.NON_BLOCKING_ERROR,
            blocking_error=HookBlockingError(
                blocking_error=str(e),
                command=command,
            ),
        )


async def run_hooks_for_event(
    event: HookEvent,
    hooks_config: dict[str, Any],
    hook_input: HookInput,
) -> list[HookResult]:
    """Run all hooks configured for a given event."""
    event_hooks = hooks_config.get(event.value, [])
    if not event_hooks:
        return []

    results: list[HookResult] = []
    for hook in event_hooks:
        if isinstance(hook, str):
            result = await run_hook_command(hook, hook_input)
            results.append(result)
        elif isinstance(hook, dict):
            command = hook.get("command", "")
            timeout = hook.get("timeout", 30.0)
            if command:
                result = await run_hook_command(command, hook_input, timeout=timeout)
                results.append(result)

    return results
