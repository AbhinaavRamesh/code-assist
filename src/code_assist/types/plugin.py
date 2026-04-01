"""Plugin system types.

Ports the TypeScript plugin types from src/types/plugin.ts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PluginManifest:
    """Manifest describing a plugin's capabilities."""

    name: str = ""
    version: str = ""
    description: str = ""
    repository: str = ""
    author: str = ""
    hooks: dict[str, Any] = field(default_factory=dict)
    tools: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadedPlugin:
    """A plugin that has been loaded and is active."""

    manifest: PluginManifest = field(default_factory=PluginManifest)
    path: str = ""
    source: str = ""
    is_active: bool = True
    error: str | None = None
