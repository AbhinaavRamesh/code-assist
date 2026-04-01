"""The /compact slash command."""

from claude_code.types.command import CommandBase, CommandType

compact_command = CommandBase(
    name="compact",
    description="Compact the conversation to reduce context size",
    command_type=CommandType.PROMPT,
    user_invocable=True,
    progress_message="Compacting conversation...",
)
