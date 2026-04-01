"""Plugin discovery and loading system."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from claude_code.config.constants import get_claude_dir
from claude_code.types.hooks import HookEvent
from claude_code.types.plugin import LoadedPlugin, PluginManifest

logger = logging.getLogger(__name__)


def get_plugins_dir() -> Path:
    """Get the user plugins directory."""
    return get_claude_dir() / "plugins"


def discover_plugins(plugins_dir: Path | None = None) -> list[Path]:
    """Discover plugin directories containing manifest.json."""
    directory = plugins_dir or get_plugins_dir()
    if not directory.exists():
        return []

    plugins: list[Path] = []
    for child in sorted(directory.iterdir()):
        if child.is_dir():
            manifest_path = child / "manifest.json"
            if manifest_path.exists():
                plugins.append(child)
    return plugins


def load_plugin_manifest(plugin_dir: Path) -> PluginManifest | None:
    """Load a plugin manifest from a directory."""
    manifest_path = plugin_dir / "manifest.json"
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return PluginManifest(
            name=data.get("name", plugin_dir.name),
            version=data.get("version", "0.0.0"),
            description=data.get("description", ""),
            repository=data.get("repository", ""),
            author=data.get("author", ""),
            hooks=data.get("hooks", {}),
            tools=data.get("tools", []),
            commands=data.get("commands", []),
            settings=data.get("settings", {}),
        )
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load plugin manifest at %s: %s", manifest_path, e)
        return None


def load_all_plugins(plugins_dir: Path | None = None) -> tuple[list[LoadedPlugin], list[LoadedPlugin]]:
    """Load all plugins, returning (enabled, disabled) lists."""
    enabled: list[LoadedPlugin] = []
    disabled: list[LoadedPlugin] = []

    for plugin_path in discover_plugins(plugins_dir):
        manifest = load_plugin_manifest(plugin_path)
        if manifest is None:
            disabled.append(
                LoadedPlugin(
                    path=str(plugin_path),
                    source="user",
                    is_active=False,
                    error="Failed to parse manifest",
                )
            )
            continue

        enabled.append(
            LoadedPlugin(
                manifest=manifest,
                path=str(plugin_path),
                source="user",
                is_active=True,
            )
        )

    return enabled, disabled


def get_plugin_hooks(
    plugins: list[LoadedPlugin],
    event: HookEvent,
) -> list[dict[str, Any]]:
    """Get hook configurations from all plugins for a given event."""
    hooks: list[dict[str, Any]] = []
    for plugin in plugins:
        if not plugin.is_active:
            continue
        plugin_hooks = plugin.manifest.hooks.get(event.value, [])
        for hook in plugin_hooks:
            if isinstance(hook, str):
                hooks.append({"command": hook, "plugin": plugin.manifest.name})
            elif isinstance(hook, dict):
                hooks.append({**hook, "plugin": plugin.manifest.name})
    return hooks
