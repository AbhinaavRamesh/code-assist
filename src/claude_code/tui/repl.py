"""REPL screen with message list and prompt input."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget

from claude_code.tui.widgets.message_list import MessageList, MessageRole
from claude_code.tui.widgets.prompt_input import PromptInput
from claude_code.tui.widgets.spinner import Spinner
from claude_code.tui.widgets.status_line import StatusLine


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""

    role: MessageRole
    content: str
    tool_name: str | None = None
    tool_input: str | None = None


class REPLScreen(Widget):
    """Container widget that composes the message list, spinner, input, and status bar."""

    DEFAULT_CSS = """
    REPLScreen {
        layout: vertical;
        height: 1fr;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._history: List[ConversationTurn] = []

    # -- Compose ---------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield MessageList(id="message-list")
        yield Spinner(id="spinner")
        yield PromptInput(id="prompt-area")
        yield StatusLine(id="status-bar")

    # -- Event handlers --------------------------------------------------------

    def on_mount(self) -> None:
        """Hide the spinner on startup."""
        self.query_one("#spinner", Spinner).visible = False

    def on_prompt_input_submitted(self, event: PromptInput.Submitted) -> None:
        """Handle user submitting a message from the prompt."""
        text = event.value.strip()
        if not text:
            return

        # Record and display the user message.
        turn = ConversationTurn(role="user", content=text)
        self._history.append(turn)
        self.query_one("#message-list", MessageList).add_message("user", text)

        # Show thinking spinner.
        spinner = self.query_one("#spinner", Spinner)
        spinner.mode = "thinking"
        spinner.visible = True

        # Post a message so the app (or a service layer) can react.
        self.post_message(self.UserSubmitted(text))

    # -- Public API ------------------------------------------------------------

    def show_assistant_response(self, content: str) -> None:
        """Display an assistant response and hide the spinner."""
        turn = ConversationTurn(role="assistant", content=content)
        self._history.append(turn)
        self.query_one("#message-list", MessageList).add_message("assistant", content)
        self.query_one("#spinner", Spinner).visible = False

    def show_tool_use(self, tool_name: str, tool_input: str) -> None:
        """Display a tool-use block."""
        turn = ConversationTurn(
            role="tool", content=f"Tool: {tool_name}", tool_name=tool_name, tool_input=tool_input
        )
        self._history.append(turn)
        self.query_one("#message-list", MessageList).add_tool_use(tool_name, tool_input)
        spinner = self.query_one("#spinner", Spinner)
        spinner.mode = "tool_use"
        spinner.status_text = tool_name

    def show_system_message(self, content: str) -> None:
        """Display a system-level informational message."""
        turn = ConversationTurn(role="system", content=content)
        self._history.append(turn)
        self.query_one("#message-list", MessageList).add_message("system", content)

    def clear_messages(self) -> None:
        """Remove all messages from the display and history."""
        self._history.clear()
        self.query_one("#message-list", MessageList).clear()

    def update_status(
        self,
        *,
        model: str | None = None,
        tokens: int | None = None,
        cost: float | None = None,
        tool: str | None = None,
    ) -> None:
        """Update the bottom status bar."""
        status = self.query_one("#status-bar", StatusLine)
        if model is not None:
            status.model_name = model
        if tokens is not None:
            status.token_count = tokens
        if cost is not None:
            status.session_cost = cost
        if tool is not None:
            status.active_tool = tool

    # -- Custom messages -------------------------------------------------------

    class UserSubmitted(Message):
        """Posted when the user submits a prompt."""

        def __init__(self, value: str) -> None:
            super().__init__()
            self.value = value
