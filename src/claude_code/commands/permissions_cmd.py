"""The /permissions slash command."""

from claude_code.types.command import CommandBase, CommandType

permissions_command = CommandBase(
    name="permissions",
    description="View or manage tool permissions",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
