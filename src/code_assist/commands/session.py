"""The /session slash command."""

from code_assist.types.command import CommandBase, CommandType

session_command = CommandBase(
    name="session",
    description="Manage conversation sessions",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
