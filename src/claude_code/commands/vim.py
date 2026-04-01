"""The /vim slash command."""

from claude_code.types.command import CommandBase, CommandType

vim_command = CommandBase(
    name="vim",
    description="Toggle vim keybinding mode",
    command_type=CommandType.LOCAL,
    user_invocable=True,
)
