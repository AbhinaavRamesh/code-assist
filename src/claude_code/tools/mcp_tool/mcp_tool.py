"""MCPTool - delegates tool execution to an MCP (Model Context Protocol) server.

Wraps MCP server tools discovered via the MCP client. Each MCP tool is
exposed with a normalized name (mcp__server__tool) and delegates execution
to the MCP client session.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel, Field

from claude_code.services.mcp.client import MCPConnection, normalize_tool_name
from claude_code.tools.base import (
    CanUseToolFn,
    DescriptionOptions,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
    ValidationResult,
)
from claude_code.types.message import AssistantMessage

logger = logging.getLogger(__name__)


class MCPToolInput(BaseModel):
    """Input schema for MCPTool.

    Accepts arbitrary arguments since each MCP tool defines its own schema.
    The server_name and tool_name route the call to the correct MCP server.
    """

    server_name: str = Field(
        ..., description="Name of the MCP server to call"
    )
    tool_name: str = Field(
        ..., description="Name of the tool on the MCP server"
    )
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments to pass to the MCP tool",
    )


class MCPTool(ToolDef):
    """Delegate tool execution to an MCP server.

    Looks up the correct MCP client connection from context.mcp_clients
    and invokes the specified tool. Results are returned as text content.
    """

    name = "MCPTool"
    max_result_size_chars = 100_000
    is_mcp = True

    @property
    def input_schema(self) -> type[BaseModel]:
        return MCPToolInput

    def _find_connection(
        self, context: ToolUseContext, server_name: str
    ) -> MCPConnection | None:
        """Find the MCP connection for the given server name."""
        for client in context.mcp_clients:
            if isinstance(client, MCPConnection):
                if client.config.name == server_name:
                    return client
            elif isinstance(client, dict):
                if client.get("name") == server_name or client.get("config", {}).get("name") == server_name:
                    return client  # type: ignore[return-value]
        return None

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        inp: MCPToolInput = input  # type: ignore[assignment]
        if not inp.server_name.strip():
            return ValidationResult(
                result=False, message="server_name is required", error_code=1
            )
        if not inp.tool_name.strip():
            return ValidationResult(
                result=False, message="tool_name is required", error_code=2
            )
        return ValidationResult(result=True)

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        inp: MCPToolInput = args  # type: ignore[assignment]

        connection = self._find_connection(context, inp.server_name)
        if connection is None:
            return ToolResult(
                data=f"MCP server not found: {inp.server_name}. "
                "Available servers may not be connected.",
                mcp_meta={"error": "server_not_found"},
            )

        # Attempt real MCP call via the mcp SDK
        try:
            result_text = await self._invoke_mcp_tool(
                connection, inp.tool_name, inp.arguments
            )
            return ToolResult(
                data=result_text,
                mcp_meta={
                    "server": inp.server_name,
                    "tool": inp.tool_name,
                    "normalized_name": normalize_tool_name(
                        inp.server_name, inp.tool_name
                    ),
                },
            )
        except Exception as exc:
            logger.warning(
                "MCP tool call failed: %s/%s: %s",
                inp.server_name,
                inp.tool_name,
                exc,
            )
            return ToolResult(
                data=f"MCP tool call failed: {exc}",
                mcp_meta={"error": str(exc)},
            )

    async def _invoke_mcp_tool(
        self,
        connection: MCPConnection | dict,  # type: ignore[type-arg]
        tool_name: str,
        arguments: dict[str, Any],
    ) -> str:
        """Invoke the tool on the MCP server via the mcp SDK."""
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            if isinstance(connection, MCPConnection):
                config = connection.config
            else:
                # dict-based connection
                config_dict = connection.get("config", connection)  # type: ignore[union-attr]
                from claude_code.services.mcp.client import MCPServerConfig

                config = MCPServerConfig(
                    name=config_dict.get("name", ""),
                    command=config_dict.get("command", ""),
                    args=config_dict.get("args", []),
                    env=config_dict.get("env", {}),
                )

            if config.command:
                params = StdioServerParameters(
                    command=config.command,
                    args=config.args,
                    env=config.env or None,
                )
                async with stdio_client(params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments)
                        # Extract text content from the result
                        if hasattr(result, "content"):
                            parts = []
                            for block in result.content:
                                if hasattr(block, "text"):
                                    parts.append(block.text)
                                else:
                                    parts.append(str(block))
                            return "\n".join(parts)
                        return str(result)
            else:
                return f"MCP server has no command configured"

        except ImportError:
            return (
                f"MCP call to {tool_name} with "
                f"{json.dumps(arguments, default=str)[:200]} "
                "(mcp package not installed)"
            )

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        inp: MCPToolInput = input  # type: ignore[assignment]
        return f"MCP: {inp.server_name}/{inp.tool_name}"

    def is_read_only(self, input: BaseModel) -> bool:
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return False
