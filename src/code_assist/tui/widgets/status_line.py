"""Bottom status bar showing model, tokens, cost, and active tool."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class StatusLine(Widget):
    """A single-line status bar docked to the bottom of the screen.

    Displays four reactive segments:
    - Model name
    - Token count
    - Session cost (USD)
    - Active tool name
    """

    DEFAULT_CSS = """
    StatusLine {
        height: 1;
        dock: bottom;
        background: $surface;
        color: $text;
        layout: horizontal;
        padding: 0 1;
    }

    StatusLine .status-segment {
        width: 1fr;
    }

    StatusLine .status-model {
        text-align: left;
        color: #7c3aed;
    }

    StatusLine .status-tokens {
        text-align: center;
        color: #06b6d4;
    }

    StatusLine .status-cost {
        text-align: center;
        color: #10b981;
    }

    StatusLine .status-tool {
        text-align: right;
        color: #f59e0b;
    }
    """

    model_name: reactive[str] = reactive("claude-sonnet-4-20250514")
    token_count: reactive[int] = reactive(0)
    session_cost: reactive[float] = reactive(0.0)
    active_tool: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Static(self.model_name, classes="status-segment status-model", id="status-model")
            yield Static(
                self._format_tokens(), classes="status-segment status-tokens", id="status-tokens"
            )
            yield Static(
                self._format_cost(), classes="status-segment status-cost", id="status-cost"
            )
            yield Static("", classes="status-segment status-tool", id="status-tool")

    # -- Reactive watchers -----------------------------------------------------

    def watch_model_name(self, value: str) -> None:
        try:
            self.query_one("#status-model", Static).update(value)
        except Exception:
            pass

    def watch_token_count(self, value: int) -> None:
        try:
            self.query_one("#status-tokens", Static).update(self._format_tokens(value))
        except Exception:
            pass

    def watch_session_cost(self, value: float) -> None:
        try:
            self.query_one("#status-cost", Static).update(self._format_cost(value))
        except Exception:
            pass

    def watch_active_tool(self, value: str) -> None:
        try:
            self.query_one("#status-tool", Static).update(value)
        except Exception:
            pass

    # -- Formatting ------------------------------------------------------------

    @staticmethod
    def _format_tokens(count: int | None = None) -> str:
        if count is None or count == 0:
            return "0 tokens"
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M tokens"
        if count >= 1_000:
            return f"{count / 1_000:.1f}k tokens"
        return f"{count} tokens"

    @staticmethod
    def _format_cost(cost: float | None = None) -> str:
        if cost is None or cost == 0.0:
            return "$0.00"
        return f"${cost:.4f}"
