"""The /memory slash command."""

from code_assist.types.command import CommandBase, CommandType

memory_command = CommandBase(
    name="memory",
    description="View or manage CLAUDE.md memory files",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
