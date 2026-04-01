"""The /tasks slash command."""

from claude_code.types.command import CommandBase, CommandType

tasks_command = CommandBase(
    name="tasks",
    description="View and manage background tasks",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
