"""Destructive command warnings.

Generates human-readable warning messages for commands that may
cause irreversible damage.
"""

from __future__ import annotations

from code_assist.tools.bash.security import analyze_command_safety
from code_assist.utils.bash.commands import is_potentially_destructive
from code_assist.utils.bash.parser import extract_command_name


def get_destructive_warning(cmd: str) -> str | None:
    """Return a warning string for destructive commands, or None if safe.

    Combines pattern-based safety analysis with command-name classification.
    """
    cmd_stripped = cmd.strip()
    if not cmd_stripped:
        return None

    # Check pattern-based safety first (highest priority)
    safety = analyze_command_safety(cmd_stripped)
    if not safety.is_safe:
        return (
            f"DANGER ({safety.risk_level}): {safety.reason}. "
            f"This command may cause irreversible damage."
        )

    # Check if the base command is in the destructive set
    if is_potentially_destructive(cmd_stripped):
        name = extract_command_name(cmd_stripped)
        return (
            f"Warning: '{name}' is a potentially destructive command. "
            f"Please review carefully before proceeding."
        )

    return None
