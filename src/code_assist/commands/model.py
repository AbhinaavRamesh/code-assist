"""The /model slash command."""

from code_assist.types.command import CommandBase, CommandType

model_command = CommandBase(
    name="model",
    description="Show or change the current model",
    command_type=CommandType.LOCAL,
    user_invocable=True,
    argument_hint="[model-name]",
)
