"""The /diff slash command."""

from claude_code.types.command import CommandBase, CommandType

diff_command = CommandBase(
    name="diff",
    description="Show changes made in this session",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
