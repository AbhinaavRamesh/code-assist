"""The /commit slash command."""

from code_assist.types.command import CommandBase, CommandType

commit_command = CommandBase(
    name="commit",
    description="Generate a commit message and commit changes",
    command_type=CommandType.PROMPT,
    user_invocable=True,
    progress_message="Generating commit...",
)
