"""The /diff slash command."""

from code_assist.types.command import CommandBase, CommandType

diff_command = CommandBase(
    name="diff",
    description="Show changes made in this session",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
