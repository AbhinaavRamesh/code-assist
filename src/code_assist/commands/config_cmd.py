"""The /config slash command."""

from code_assist.types.command import CommandBase, CommandType

config_command = CommandBase(
    name="config",
    description="View or modify configuration settings",
    command_type=CommandType.LOCAL,
    user_invocable=True,
    argument_hint="[key] [value]",
)
