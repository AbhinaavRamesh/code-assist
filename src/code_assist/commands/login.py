"""The /login slash command."""

from code_assist.types.command import CommandBase, CommandType

login_command = CommandBase(
    name="login",
    description="Authenticate with Anthropic",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
