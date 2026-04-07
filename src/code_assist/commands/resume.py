"""The /resume slash command."""

from code_assist.types.command import CommandBase, CommandType

resume_command = CommandBase(
    name="resume",
    description="Resume a previous conversation session",
    command_type=CommandType.LOCAL,
    user_invocable=True,
    argument_hint="[session-id]",
)
