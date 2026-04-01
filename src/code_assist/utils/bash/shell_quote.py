"""Shell argument quoting utilities.

Provides safe quoting for constructing shell commands programmatically.
"""

from __future__ import annotations

import shlex


def quote_arg(arg: str) -> str:
    """Safely quote a single shell argument.

    Uses shlex.quote which wraps the argument in single quotes
    and escapes any existing single quotes.
    """
    return shlex.quote(arg)


def join_command(args: list[str]) -> str:
    """Join a list of arguments into a safely quoted shell command string.

    Each argument is individually quoted only if necessary.
    """
    return " ".join(shlex.quote(arg) for arg in args)
