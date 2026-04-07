"""Shell rule matching for bash permission rules.

Provides glob-style wildcard matching used to compare bash commands
against permission rule patterns.
"""

from __future__ import annotations

import fnmatch
import re


def normalize_rule_pattern(pattern: str) -> str:
    """Normalize a shell permission rule pattern.

    Strips leading/trailing whitespace, collapses consecutive whitespace
    to a single space, and removes a trailing semicolon if present.
    """
    normalized = re.sub(r"\s+", " ", pattern.strip())
    if normalized.endswith(";"):
        normalized = normalized[:-1].rstrip()
    return normalized


def matches_shell_pattern(pattern: str, command: str) -> bool:
    """Return True if *command* matches the glob-style *pattern*.

    Both the pattern and the command are normalized before comparison.
    An empty pattern matches nothing.  A lone ``*`` matches everything.

    The matching is performed by ``fnmatch`` which supports ``*``, ``?``,
    ``[seq]``, and ``[!seq]`` wildcards.
    """
    norm_pattern = normalize_rule_pattern(pattern)
    norm_command = normalize_rule_pattern(command)

    if not norm_pattern:
        return False

    return fnmatch.fnmatch(norm_command, norm_pattern)
