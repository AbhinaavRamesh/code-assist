"""The /theme slash command."""

from code_assist.types.command import CommandBase, CommandType

theme_command = CommandBase(
    name="theme",
    description="Change the UI theme",
    command_type=CommandType.LOCAL,
    user_invocable=True,
    argument_hint="[theme-name]",
)
