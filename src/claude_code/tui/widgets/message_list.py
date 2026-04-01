"""Scrollable message list widget with role-based styling."""

from __future__ import annotations

from typing import Literal

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Collapsible, Markdown, Static

MessageRole = Literal["user", "assistant", "system", "tool"]


class _UserBubble(Static):
    """Right-aligned blue message bubble for user messages."""

    DEFAULT_CSS = """
    _UserBubble {
        width: 100%;
        content-align-horizontal: right;
        text-align: right;
        color: #3b82f6;
        padding: 0 2 1 4;
        margin: 0 0 1 0;
    }
    """


class _AssistantBubble(Widget):
    """Left-aligned green message rendered as Markdown."""

    DEFAULT_CSS = """
    _AssistantBubble {
        width: 100%;
        padding: 0 4 1 2;
        margin: 0 0 1 0;
    }

    _AssistantBubble Markdown {
        color: #10b981;
    }
    """

    def __init__(self, content: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._content = content

    def compose(self) -> ComposeResult:
        yield Markdown(self._content)


class _SystemBubble(Static):
    """Centered dim message for system notifications."""

    DEFAULT_CSS = """
    _SystemBubble {
        width: 100%;
        content-align-horizontal: center;
        text-align: center;
        color: #6b7280;
        text-style: dim;
        padding: 0 2 1 2;
        margin: 0 0 1 0;
    }
    """


class _ToolUseBubble(Widget):
    """Collapsible block showing tool invocation details."""

    DEFAULT_CSS = """
    _ToolUseBubble {
        width: 100%;
        padding: 0 2 1 2;
        margin: 0 0 1 0;
    }

    _ToolUseBubble Collapsible {
        border: tall #6b7280;
        padding: 0 1;
    }

    _ToolUseBubble .tool-input {
        color: #9ca3af;
        padding: 0 1;
    }
    """

    def __init__(self, tool_name: str, tool_input: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._tool_name = tool_name
        self._tool_input = tool_input

    def compose(self) -> ComposeResult:
        with Collapsible(title=f"Tool: {self._tool_name}", collapsed=True):
            yield Static(self._tool_input, classes="tool-input")


class MessageList(VerticalScroll):
    """Scrollable container that holds conversation messages.

    Messages are displayed with role-specific styling:
    - **user**: right-aligned, blue
    - **assistant**: left-aligned, green, Markdown-rendered
    - **system**: centered, dim
    - **tool**: collapsible detail block
    """

    DEFAULT_CSS = """
    MessageList {
        height: 1fr;
        overflow-y: auto;
        padding: 1;
    }
    """

    message_count: reactive[int] = reactive(0)

    def add_message(self, role: MessageRole, content: str) -> None:
        """Append a message bubble for the given *role*."""
        if role == "user":
            widget = _UserBubble(content)
        elif role == "assistant":
            widget = _AssistantBubble(content)
        elif role == "system":
            widget = _SystemBubble(content)
        else:
            widget = _SystemBubble(content)

        self.mount(widget)
        self.message_count += 1
        self.scroll_end(animate=False)

    def add_tool_use(self, tool_name: str, tool_input: str) -> None:
        """Append a collapsible tool-use block."""
        widget = _ToolUseBubble(tool_name, tool_input)
        self.mount(widget)
        self.message_count += 1
        self.scroll_end(animate=False)

    def clear(self) -> None:
        """Remove all message widgets."""
        for child in list(self.children):
            child.remove()
        self.message_count = 0
