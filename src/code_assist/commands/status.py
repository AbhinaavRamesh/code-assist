"""The /status slash command."""

from code_assist.types.command import CommandBase, CommandType

status_command = CommandBase(
    name="status",
    description="Show current status and context information",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
