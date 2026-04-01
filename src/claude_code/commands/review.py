"""The /review slash command."""

from claude_code.types.command import CommandBase, CommandType

review_command = CommandBase(
    name="review",
    description="Review code changes for issues",
    command_type=CommandType.PROMPT,
    user_invocable=True,
    progress_message="Reviewing changes...",
)
