"""SSE stream event processing and content block accumulation."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from claude_code.types.message import (
    AssistantMessage,
    ContentBlock,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    Usage,
)

logger = logging.getLogger(__name__)


@dataclass
class StreamAccumulator:
    """Accumulates streaming events into a complete assistant message."""

    message_id: str = ""
    model: str = ""
    content_blocks: list[ContentBlock] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    stop_reason: str | None = None
    _current_block_index: int = -1
    _current_text: str = ""
    _current_tool_input_json: str = ""

    def handle_event(self, event: Any) -> None:
        """Process a single stream event."""
        event_type = getattr(event, "type", str(event))

        if event_type == "message_start":
            msg = getattr(event, "message", None)
            if msg:
                self.message_id = getattr(msg, "id", "")
                self.model = getattr(msg, "model", "")
                usage = getattr(msg, "usage", None)
                if usage:
                    self.usage.input_tokens = getattr(usage, "input_tokens", 0)

        elif event_type == "content_block_start":
            block = getattr(event, "content_block", None)
            self._current_block_index = getattr(event, "index", -1)
            self._current_text = ""
            self._current_tool_input_json = ""

            if block:
                block_type = getattr(block, "type", "")
                if block_type == "text":
                    self.content_blocks.append(TextBlock(text=""))
                elif block_type == "tool_use":
                    self.content_blocks.append(
                        ToolUseBlock(
                            id=getattr(block, "id", ""),
                            name=getattr(block, "name", ""),
                            input={},
                        )
                    )
                elif block_type == "thinking":
                    self.content_blocks.append(ThinkingBlock(thinking=""))

        elif event_type == "content_block_delta":
            delta = getattr(event, "delta", None)
            if delta and self.content_blocks:
                delta_type = getattr(delta, "type", "")
                block = self.content_blocks[-1]

                if delta_type == "text_delta" and isinstance(block, TextBlock):
                    text = getattr(delta, "text", "")
                    block.text += text

                elif delta_type == "input_json_delta" and isinstance(block, ToolUseBlock):
                    json_chunk = getattr(delta, "partial_json", "")
                    self._current_tool_input_json += json_chunk

                elif delta_type == "thinking_delta" and isinstance(block, ThinkingBlock):
                    thinking = getattr(delta, "thinking", "")
                    block.thinking += thinking

        elif event_type == "content_block_stop":
            if self.content_blocks:
                block = self.content_blocks[-1]
                if isinstance(block, ToolUseBlock) and self._current_tool_input_json:
                    import json

                    try:
                        block.input = json.loads(self._current_tool_input_json)
                    except json.JSONDecodeError:
                        block.input = {"_raw": self._current_tool_input_json}
                    self._current_tool_input_json = ""

        elif event_type == "message_delta":
            delta = getattr(event, "delta", None)
            if delta:
                self.stop_reason = getattr(delta, "stop_reason", None)
            usage = getattr(event, "usage", None)
            if usage:
                self.usage.output_tokens = getattr(usage, "output_tokens", 0)

        elif event_type == "message_stop":
            pass

    def to_message(self) -> AssistantMessage:
        """Convert accumulated state to an AssistantMessage."""
        return AssistantMessage(
            id=self.message_id,
            content=self.content_blocks,
            model=self.model,
            stop_reason=self.stop_reason,
            usage=self.usage,
        )

    def get_tool_use_blocks(self) -> list[ToolUseBlock]:
        """Get all tool_use blocks from the accumulated content."""
        return [b for b in self.content_blocks if isinstance(b, ToolUseBlock)]

    def get_text(self) -> str:
        """Get concatenated text from all text blocks."""
        return "".join(
            b.text for b in self.content_blocks if isinstance(b, TextBlock)
        )
