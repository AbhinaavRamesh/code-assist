"""Sandbox decision logic.

Determines whether a command should be executed inside a sandbox
environment for additional safety.
"""

from __future__ import annotations

from claude_code.tools.bash.command_semantics import classify_command
from claude_code.tools.bash.read_only_validation import validate_read_only
from claude_code.tools.bash.security import analyze_command_safety
from claude_code.utils.bash.commands import is_potentially_destructive


def should_use_sandbox(cmd: str) -> bool:
    """Determine whether a command should be run inside a sandbox.

    Sandboxing is recommended when:
    - The command is potentially destructive
    - The command has dangerous patterns
    - The command performs writes or network access
    - The command is not verified as read-only

    Read-only commands can safely skip the sandbox.
    """
    cmd_stripped = cmd.strip()
    if not cmd_stripped:
        return False

    # Definitely sandbox destructive commands
    if is_potentially_destructive(cmd_stripped):
        return True

    # Sandbox commands with dangerous patterns
    safety = analyze_command_safety(cmd_stripped)
    if not safety.is_safe:
        return True

    # Read-only commands don't need sandboxing
    if validate_read_only(cmd_stripped):
        return False

    # Commands with write or network semantics should be sandboxed
    semantics = classify_command(cmd_stripped)
    if semantics.is_write or semantics.is_network:
        return True

    return False
