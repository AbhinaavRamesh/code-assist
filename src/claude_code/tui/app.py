"""Main Textual application for the Claude Code TUI."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

from claude_code.tui.repl import REPLScreen


class ClaudeCodeApp(App):
    """Top-level Textual application that hosts the REPL interface."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #message-list {
        height: 1fr;
        overflow-y: auto;
        padding: 1;
    }

    #prompt-area {
        height: auto;
        max-height: 10;
        dock: bottom;
    }

    #status-bar {
        height: 1;
        dock: bottom;
        background: $surface;
    }
    """

    TITLE = "Claude Code"

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+l", "clear", "Clear"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield REPLScreen()
        yield Footer()

    def action_clear(self) -> None:
        """Clear all messages from the REPL screen."""
        self.query_one(REPLScreen).clear_messages()
