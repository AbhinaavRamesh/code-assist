"""The /resume slash command."""

from claude_code.types.command import CommandBase, CommandType

resume_command = CommandBase(
    name="resume",
    description="Resume a previous conversation session",
    command_type=CommandType.LOCAL,
    user_invocable=True,
    argument_hint="[session-id]",
)
