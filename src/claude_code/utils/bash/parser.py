"""Shell command parsing utilities.

Provides functions for splitting and analyzing shell commands.
"""

from __future__ import annotations

import re
import shlex


def parse_command(cmd: str) -> list[str]:
    """Split a shell command into parts using shlex.

    Handles quoted strings and escape characters properly.
    Returns an empty list for empty/whitespace-only commands.
    Falls back to simple split on parse errors.
    """
    cmd = cmd.strip()
    if not cmd:
        return []
    try:
        return shlex.split(cmd)
    except ValueError:
        # Fallback for malformed commands (unclosed quotes, etc.)
        return cmd.split()


def extract_command_name(cmd: str) -> str:
    """Get the base command name from a shell command string.

    Strips env var assignments and path prefixes.
    Returns empty string if no command can be extracted.

    Examples:
        "ls -la" -> "ls"
        "/usr/bin/git status" -> "git"
        "VAR=1 command" -> "command"
        "sudo rm -rf /" -> "sudo"
    """
    parts = parse_command(cmd)
    if not parts:
        return ""

    # Skip leading env var assignments (FOO=bar)
    idx = 0
    while idx < len(parts) and "=" in parts[idx] and not parts[idx].startswith("="):
        # Ensure it looks like a valid var assignment (starts with letter/underscore)
        name = parts[idx].split("=", 1)[0]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            idx += 1
        else:
            break

    if idx >= len(parts):
        return ""

    # Strip path prefix to get bare command name
    name = parts[idx]
    # Remove path prefix (e.g., /usr/bin/git -> git)
    if "/" in name:
        name = name.rsplit("/", 1)[-1]
    return name


def is_piped_command(cmd: str) -> bool:
    """Check if a command contains pipe operators.

    Detects | but not || (logical OR).
    """
    # Remove quoted strings to avoid false positives
    stripped = _remove_quoted_strings(cmd)
    # Match | that is not preceded or followed by another |
    return bool(re.search(r"(?<!\|)\|(?!\|)", stripped))


def split_chained_commands(cmd: str) -> list[str]:
    """Split a command string on chain operators (&&, ||, ;).

    Does not split on operators inside quoted strings.
    Returns a list of individual command strings, stripped of whitespace.
    """
    stripped = _remove_quoted_strings(cmd)

    # Find positions of chain operators in the stripped version
    # We need to split the original string at the same positions
    parts: list[str] = []
    # Use a regex to split on &&, ||, or ; outside of quotes
    # Since we can't easily do this with regex on the original string,
    # we'll use a character-by-character approach
    result: list[str] = []
    current: list[str] = []
    i = 0
    in_single_quote = False
    in_double_quote = False
    escaped = False

    while i < len(cmd):
        ch = cmd[i]

        if escaped:
            current.append(ch)
            escaped = False
            i += 1
            continue

        if ch == "\\" and not in_single_quote:
            escaped = True
            current.append(ch)
            i += 1
            continue

        if ch == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current.append(ch)
            i += 1
            continue

        if ch == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current.append(ch)
            i += 1
            continue

        if in_single_quote or in_double_quote:
            current.append(ch)
            i += 1
            continue

        # Check for chain operators
        if ch == ";" :
            result.append("".join(current).strip())
            current = []
            i += 1
            continue

        if ch == "&" and i + 1 < len(cmd) and cmd[i + 1] == "&":
            result.append("".join(current).strip())
            current = []
            i += 2
            continue

        if ch == "|" and i + 1 < len(cmd) and cmd[i + 1] == "|":
            result.append("".join(current).strip())
            current = []
            i += 2
            continue

        current.append(ch)
        i += 1

    # Add final segment
    final = "".join(current).strip()
    if final:
        result.append(final)

    # Filter out empty strings
    return [part for part in result if part]


def _remove_quoted_strings(cmd: str) -> str:
    """Remove single and double quoted strings from a command.

    Used internally to avoid false positives when searching for operators.
    """
    result: list[str] = []
    i = 0
    in_single_quote = False
    in_double_quote = False
    escaped = False

    while i < len(cmd):
        ch = cmd[i]

        if escaped:
            if not in_single_quote and not in_double_quote:
                result.append(ch)
            escaped = False
            i += 1
            continue

        if ch == "\\" and not in_single_quote:
            escaped = True
            if not in_single_quote and not in_double_quote:
                result.append(ch)
            i += 1
            continue

        if ch == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            i += 1
            continue

        if ch == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            i += 1
            continue

        if not in_single_quote and not in_double_quote:
            result.append(ch)

        i += 1

    return "".join(result)
