"""Settings management - loading, merging, and persisting settings.

Settings management - loading, merging, and persisting settings.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from code_assist.config.constants import (
    get_global_settings_path,
    get_local_settings_path,
    get_project_settings_path,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Settings JSON Schema (simplified Pydantic-compatible dict)
# ---------------------------------------------------------------------------


def get_default_settings() -> dict[str, Any]:
    """Return default settings matching TS SettingsJson."""
    return {
        "permissions": {
            "allow": [],
            "deny": [],
        },
        "hooks": {},
        "env": {},
        "mcpServers": {},
        "advancedSettings": {
            "SKIP_GIT_INSTRUCTIONS": False,
            "CLAUDE_CODE_DISABLE_CLAUDE_MDS": False,
            "DISABLE_BACKGROUND_TASKS": False,
            "DISABLE_COMPACT": False,
        },
        "plugins": [],
        "skills": {},
    }


# ---------------------------------------------------------------------------
# Settings Loading
# ---------------------------------------------------------------------------


def load_settings_file(path: Path) -> dict[str, Any]:
    """Load a settings JSON file. Returns empty dict if not found or invalid."""
    try:
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if text.strip():
                return json.loads(text)  # type: ignore[no-any-return]
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load settings from %s: %s", path, e)
    return {}


def save_settings_file(path: Path, settings: dict[str, Any]) -> None:
    """Save settings to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge override into base (override wins)."""
    result = base.copy()
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_merged_settings(project_root: str | None = None) -> dict[str, Any]:
    """Load and merge settings from all sources.

    Priority (highest wins):
    1. Local settings (.claude/settings.local.json)
    2. Project settings (.claude/settings.json)
    3. Global settings (~/.claude/settings.json)
    4. Defaults
    """
    settings = get_default_settings()

    # Global settings
    global_settings = load_settings_file(get_global_settings_path())
    settings = _deep_merge(settings, global_settings)

    # Project settings
    if project_root:
        project_settings = load_settings_file(
            get_project_settings_path(project_root)
        )
        settings = _deep_merge(settings, project_settings)

        # Local settings (highest priority)
        local_settings = load_settings_file(
            get_local_settings_path(project_root)
        )
        settings = _deep_merge(settings, local_settings)

    return settings


# ---------------------------------------------------------------------------
# Settings Access Helpers
# ---------------------------------------------------------------------------


def get_permission_rules(
    settings: dict[str, Any],
    behavior: str,
) -> list[str]:
    """Get permission rules for a given behavior (allow/deny)."""
    perms = settings.get("permissions", {})
    return perms.get(behavior, [])


def get_hooks_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Get hooks configuration."""
    return settings.get("hooks", {})


def get_mcp_servers(settings: dict[str, Any]) -> dict[str, Any]:
    """Get MCP server configuration."""
    return settings.get("mcpServers", {})


def get_env_vars(settings: dict[str, Any]) -> dict[str, str]:
    """Get environment variable overrides."""
    return settings.get("env", {})


def get_advanced_setting(
    settings: dict[str, Any],
    key: str,
    default: Any = None,
) -> Any:
    """Get an advanced setting value."""
    return settings.get("advancedSettings", {}).get(key, default)
