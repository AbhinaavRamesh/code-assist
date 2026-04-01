"""The /version slash command."""

from code_assist.types.command import CommandBase, CommandType

version_command = CommandBase(
    name="version",
    description="Show the current version",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
