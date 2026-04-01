"""The /hooks slash command."""

from claude_code.types.command import CommandBase, CommandType

hooks_command = CommandBase(
    name="hooks",
    description="View and manage hooks configuration",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
