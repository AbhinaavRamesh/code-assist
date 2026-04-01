"""Sed command analysis.

Determines whether a sed invocation modifies files in-place.
"""

from __future__ import annotations

from claude_code.utils.bash.parser import parse_command


def is_sed_edit(cmd: str) -> bool:
    """Check if a sed command modifies files (has -i / --in-place flag).

    Returns True if the sed command will write changes back to files.
    Returns False for read-only sed (stdout-only).
    """
    parts = parse_command(cmd)
    if not parts:
        return False

    for part in parts:
        # Exact match for -i or --in-place
        if part == "-i" or part == "--in-place":
            return True
        # -i with suffix, e.g. -i.bak or -i''
        if part.startswith("-i") and len(part) > 2 and not part[1:].startswith("-"):
            # Could be -i.bak or -iSUFFIX
            return True
        # Combined short flags like -ni or -in
        if (
            part.startswith("-")
            and not part.startswith("--")
            and len(part) > 1
            and "i" in part[1:]
        ):
            # This is a combined flag that includes -i
            return True

    return False
