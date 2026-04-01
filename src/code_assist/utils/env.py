"""Environment variable utilities."""

from __future__ import annotations

import os


def get_bool_env(key: str, default: bool = False) -> bool:
    """Get a boolean environment variable."""
    value = os.environ.get(key, "").lower()
    if value in ("1", "true", "yes"):
        return True
    if value in ("0", "false", "no"):
        return False
    return default


def get_int_env(key: str, default: int = 0) -> int:
    """Get an integer environment variable."""
    try:
        return int(os.environ.get(key, str(default)))
    except ValueError:
        return default
