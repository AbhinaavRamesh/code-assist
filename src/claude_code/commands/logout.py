"""The /logout slash command."""

from claude_code.types.command import CommandBase, CommandType

logout_command = CommandBase(
    name="logout",
    description="Log out and clear stored credentials",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
