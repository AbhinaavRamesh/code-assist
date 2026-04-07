"""Process user input - route slash commands vs regular prompts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProcessedInput:
    """Result of processing user input."""

    is_command: bool = False
    command_name: str = ""
    command_args: str = ""
    prompt_text: str = ""
    attachments: list[dict[str, Any]] = field(default_factory=list)
    image_paths: list[str] = field(default_factory=list)
    file_paths: list[str] = field(default_factory=list)


def process_user_input(text: str) -> ProcessedInput:
    """Parse user input to detect slash commands, file references, etc."""
    text = text.strip()

    # Slash command detection
    if text.startswith("/"):
        parts = text.split(None, 1)
        command_name = parts[0][1:]  # Remove leading /
        command_args = parts[1] if len(parts) > 1 else ""
        return ProcessedInput(
            is_command=True,
            command_name=command_name,
            command_args=command_args,
        )

    # Shell escape (! prefix runs command)
    if text.startswith("!"):
        return ProcessedInput(
            is_command=True,
            command_name="!",
            command_args=text[1:].strip(),
        )

    return ProcessedInput(prompt_text=text)
