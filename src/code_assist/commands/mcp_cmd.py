"""The /mcp slash command."""

from code_assist.types.command import CommandBase, CommandType

mcp_command = CommandBase(
    name="mcp",
    description="Manage MCP server connections",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
