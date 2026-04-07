"""The /plan slash command."""

from code_assist.types.command import CommandBase, CommandType

plan_command = CommandBase(
    name="plan",
    description="Enter plan mode for multi-step tasks",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
