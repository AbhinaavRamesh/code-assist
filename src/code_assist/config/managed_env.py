"""Managed environment variable handling."""

from __future__ import annotations

import os
from typing import Any


def apply_env_overrides(env_config: dict[str, str]) -> None:
    """Apply environment variable overrides from settings."""
    for key, value in env_config.items():
        if key not in os.environ:
            os.environ[key] = value


def get_env(key: str, default: str = "") -> str:
    """Get an environment variable with a default."""
    return os.environ.get(key, default)


def get_api_key() -> str | None:
    """Get the Anthropic API key from environment."""
    return os.environ.get("ANTHROPIC_API_KEY")


def get_api_base_url() -> str:
    """Get the Anthropic API base URL."""
    return os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return os.environ.get("CODE_ASSIST_DEBUG", "").lower() in ("1", "true")
