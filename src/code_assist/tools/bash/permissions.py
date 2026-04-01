"""Permission helpers for bash commands.

Determines whether commands can be auto-approved and generates
human-readable permission messages.
"""

from __future__ import annotations

from code_assist.tools.bash.command_semantics import classify_command
from code_assist.tools.bash.read_only_validation import validate_read_only
from code_assist.tools.bash.security import analyze_command_safety
from code_assist.utils.bash.commands import is_known_safe
from code_assist.utils.bash.parser import extract_command_name


def should_auto_approve(cmd: str) -> bool:
    """Determine if a command is safe enough to run without user confirmation.

    A command is auto-approved only when:
    - It is composed entirely of known-safe commands
    - It is read-only (no writes)
    - No dangerous patterns are detected
    """
    if not cmd.strip():
        return False

    # Must be known safe
    if not is_known_safe(cmd):
        return False

    # Must be read-only
    if not validate_read_only(cmd):
        return False

    # Must not match dangerous patterns
    safety = analyze_command_safety(cmd)
    if not safety.is_safe:
        return False

    return True


def get_permission_message(cmd: str) -> str:
    """Generate a human-readable permission description for a command.

    Describes what the command does and why permission is needed.
    """
    name = extract_command_name(cmd)
    semantics = classify_command(cmd)
    safety = analyze_command_safety(cmd)

    parts: list[str] = []

    if not safety.is_safe:
        parts.append(f"WARNING: {safety.reason}")
        parts.append(f"Risk level: {safety.risk_level}")

    actions: list[str] = []
    if semantics.is_write:
        actions.append("modify files or system state")
    if semantics.is_network:
        actions.append("access the network")
    if semantics.is_search:
        actions.append("search files")
    if semantics.is_read and not semantics.is_write:
        actions.append("read files or system information")

    if actions:
        parts.append(f"This command ({name}) will {', '.join(actions)}.")
    else:
        parts.append(f"Allow execution of: {name}?")

    return " ".join(parts)
