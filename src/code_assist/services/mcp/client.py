"""MCP client using the official Python mcp SDK."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""

    name: str = ""
    command: str = ""
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    transport: str = "stdio"  # stdio, sse, http, websocket
    url: str = ""


@dataclass
class MCPTool:
    """A tool discovered from an MCP server."""

    name: str = ""
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)
    server_name: str = ""


@dataclass
class MCPResource:
    """A resource from an MCP server."""

    uri: str = ""
    name: str = ""
    description: str = ""
    mime_type: str = ""


@dataclass
class MCPConnection:
    """An active MCP server connection."""

    config: MCPServerConfig = field(default_factory=MCPServerConfig)
    tools: list[MCPTool] = field(default_factory=list)
    resources: list[MCPResource] = field(default_factory=list)
    is_connected: bool = False
    error: str | None = None


async def connect_mcp_server(config: MCPServerConfig) -> MCPConnection:
    """Connect to an MCP server and discover tools/resources.

    Full implementation uses the mcp Python SDK with stdio/SSE/HTTP transports.
    """
    connection = MCPConnection(config=config)

    try:
        # Import the mcp SDK
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        if config.transport == "stdio" and config.command:
            params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=config.env or None,
            )
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    # Discover tools
                    tools_result = await session.list_tools()
                    for tool in tools_result.tools:
                        connection.tools.append(
                            MCPTool(
                                name=tool.name,
                                description=tool.description or "",
                                input_schema=tool.inputSchema if hasattr(tool, "inputSchema") else {},
                                server_name=config.name,
                            )
                        )

                    # Discover resources
                    try:
                        resources_result = await session.list_resources()
                        for resource in resources_result.resources:
                            connection.resources.append(
                                MCPResource(
                                    uri=str(resource.uri),
                                    name=resource.name or "",
                                    description=resource.description or "",
                                    mime_type=resource.mimeType or "",
                                )
                            )
                    except Exception:
                        pass  # Resources are optional

                    connection.is_connected = True

    except ImportError:
        connection.error = "mcp package not installed"
        logger.warning("MCP SDK not available - install with: uv add mcp")
    except Exception as e:
        connection.error = str(e)
        logger.warning("Failed to connect to MCP server %s: %s", config.name, e)

    return connection


def normalize_tool_name(server_name: str, tool_name: str) -> str:
    """Normalize MCP tool name to mcp__server__tool format."""
    safe_server = server_name.replace("-", "_").replace(" ", "_")
    safe_tool = tool_name.replace("-", "_").replace(" ", "_")
    return f"mcp__{safe_server}__{safe_tool}"
