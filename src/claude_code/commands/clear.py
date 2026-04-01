"""The /clear slash command."""

from claude_code.types.command import CommandBase, CommandType

clear_command = CommandBase(
    name="clear",
    description="Clear the conversation history",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
