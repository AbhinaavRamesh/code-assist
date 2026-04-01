"""The /cost slash command."""

from claude_code.types.command import CommandBase, CommandType

cost_command = CommandBase(
    name="cost",
    description="Show token usage and cost for this session",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
