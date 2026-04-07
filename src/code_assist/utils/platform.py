"""Platform detection utilities."""

from __future__ import annotations

import os
import platform
import sys


def is_macos() -> bool:
    return sys.platform == "darwin"


def is_linux() -> bool:
    return sys.platform == "linux"


def is_windows() -> bool:
    return sys.platform == "win32"


def get_shell() -> str:
    """Get the user's default shell."""
    return os.environ.get("SHELL", "/bin/bash")


def get_platform_info() -> dict[str, str]:
    """Get platform information for system prompt."""
    return {
        "platform": sys.platform,
        "os_version": platform.version(),
        "shell": get_shell(),
        "python_version": platform.python_version(),
    }
