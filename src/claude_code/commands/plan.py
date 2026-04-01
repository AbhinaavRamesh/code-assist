"""The /plan slash command."""

from claude_code.types.command import CommandBase, CommandType

plan_command = CommandBase(
    name="plan",
    description="Enter plan mode for multi-step tasks",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
