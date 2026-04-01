"""Theme system for the Claude Code TUI.

Provides dark and light theme palettes used throughout the interface.
"""

from __future__ import annotations

from typing import Dict

ThemePalette = Dict[str, str]

DARK_THEME: ThemePalette = {
    "primary": "#7c3aed",
    "secondary": "#06b6d4",
    "background": "#1a1a2e",
    "surface": "#16213e",
    "text": "#e2e8f0",
    "user_message": "#3b82f6",
    "assistant_message": "#10b981",
    "system_message": "#6b7280",
    "error": "#ef4444",
    "warning": "#f59e0b",
}

LIGHT_THEME: ThemePalette = {
    "primary": "#7c3aed",
    "secondary": "#0891b2",
    "background": "#ffffff",
    "surface": "#f8fafc",
    "text": "#1e293b",
    "user_message": "#2563eb",
    "assistant_message": "#059669",
    "system_message": "#9ca3af",
    "error": "#dc2626",
    "warning": "#d97706",
}

_THEMES: Dict[str, ThemePalette] = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
}


def get_theme(name: str = "dark") -> ThemePalette:
    """Return a theme palette by name.

    Args:
        name: Theme name -- ``"dark"`` or ``"light"``.

    Returns:
        The corresponding palette dict.

    Raises:
        KeyError: If *name* is not a recognised theme.
    """
    return _THEMES[name]
