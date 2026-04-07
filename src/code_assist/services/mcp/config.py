"""MCP server configuration loading from settings."""

from __future__ import annotations

import os
from typing import Any

from code_assist.services.mcp.client import MCPServerConfig


def load_mcp_configs(settings: dict[str, Any]) -> list[MCPServerConfig]:
    """Load MCP server configurations from settings."""
    servers = settings.get("mcpServers", {})
    configs: list[MCPServerConfig] = []

    for name, server_config in servers.items():
        if not isinstance(server_config, dict):
            continue

        env = dict(server_config.get("env", {}))
        # Expand environment variables in env values
        for key, value in env.items():
            if isinstance(value, str) and value.startswith("$"):
                env[key] = os.environ.get(value[1:], value)

        configs.append(
            MCPServerConfig(
                name=name,
                command=server_config.get("command", ""),
                args=server_config.get("args", []),
                env=env,
                transport=server_config.get("transport", "stdio"),
                url=server_config.get("url", ""),
            )
        )

    return configs
