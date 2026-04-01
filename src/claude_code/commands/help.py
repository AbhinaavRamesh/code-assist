"""The /help slash command."""

from claude_code.types.command import CommandBase, CommandType

help_command = CommandBase(
    name="help",
    description="Show help information",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
