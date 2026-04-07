"""Bridge configuration management."""

from __future__ import annotations

import json
import os
from pathlib import Path

from code_assist.bridge.bridge_api import BridgeConfig
from code_assist.config.constants import get_claude_dir


def get_bridge_config_path() -> Path:
    """Get the bridge config file path."""
    return get_claude_dir() / "bridge.json"


def load_bridge_config() -> BridgeConfig | None:
    """Load bridge config from file or environment."""
    # Check environment first
    port = os.environ.get("CLAUDE_CODE_BRIDGE_PORT")
    if port:
        return BridgeConfig(
            port=int(port),
            token=os.environ.get("CLAUDE_CODE_BRIDGE_TOKEN", ""),
            ide_type=os.environ.get("CLAUDE_CODE_IDE_TYPE", "vscode"),
        )

    # Check config file
    path = get_bridge_config_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return BridgeConfig(
                host=data.get("host", "localhost"),
                port=data.get("port", 0),
                token=data.get("token", ""),
                ide_type=data.get("ideType", ""),
                workspace_path=data.get("workspacePath", ""),
            )
        except (json.JSONDecodeError, OSError):
            pass

    return None
