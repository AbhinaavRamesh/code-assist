"""The /doctor slash command."""

from claude_code.types.command import CommandBase, CommandType

doctor_command = CommandBase(
    name="doctor",
    description="Run diagnostics to check for issues",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
