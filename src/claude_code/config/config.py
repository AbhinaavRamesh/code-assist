"""Global and project configuration management.

Global and project configuration management.
"""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any

from claude_code.config.constants import (
    get_claude_dir,
    get_global_config_path,
    get_project_config_dir,
    get_sessions_dir,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Global Config
# ---------------------------------------------------------------------------


def get_default_global_config() -> dict[str, Any]:
    """Return default global config matching TS GlobalConfig."""
    return {
        "numStartups": 0,
        "theme": "dark",
        "verbose": False,
        "env": {},
        "autoCompactEnabled": True,
        "showTurnDuration": False,
    }


def get_global_config() -> dict[str, Any]:
    """Load the global config from ~/.claude/config.json."""
    path = get_global_config_path()
    try:
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if text.strip():
                return json.loads(text)  # type: ignore[no-any-return]
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load global config: %s", e)
    return get_default_global_config()


def save_global_config(updates: dict[str, Any]) -> None:
    """Save updates to the global config (merge with existing)."""
    config = get_global_config()
    config.update(updates)
    path = get_global_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Project Config
# ---------------------------------------------------------------------------


def get_default_project_config() -> dict[str, Any]:
    """Return default project config matching TS ProjectConfig."""
    return {
        "allowedTools": [],
        "mcpContextUris": [],
        "projectOnboardingSeenCount": 0,
    }


def get_project_config(project_root: str) -> dict[str, Any]:
    """Load the project config from .claude/config.json."""
    path = get_project_config_dir(project_root) / "config.json"
    try:
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if text.strip():
                return json.loads(text)  # type: ignore[no-any-return]
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load project config: %s", e)
    return get_default_project_config()


def save_project_config(project_root: str, updates: dict[str, Any]) -> None:
    """Save updates to the project config (merge with existing)."""
    config = get_project_config(project_root)
    config.update(updates)
    path = get_project_config_dir(project_root) / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# User ID
# ---------------------------------------------------------------------------


def get_or_create_user_id() -> str:
    """Get or create a persistent user ID."""
    config = get_global_config()
    user_id = config.get("userId")
    if not user_id:
        user_id = str(uuid.uuid4())
        save_global_config({"userId": user_id})
    return user_id  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Session Storage
# ---------------------------------------------------------------------------


def get_session_dir(session_id: str) -> Path:
    """Get the directory for a specific session."""
    return get_sessions_dir() / session_id


def ensure_claude_dir() -> Path:
    """Ensure ~/.claude directory exists and return it."""
    claude_dir = get_claude_dir()
    claude_dir.mkdir(parents=True, exist_ok=True)
    return claude_dir


def record_startup() -> None:
    """Increment the startup counter."""
    config = get_global_config()
    config["numStartups"] = config.get("numStartups", 0) + 1
    save_global_config(config)
