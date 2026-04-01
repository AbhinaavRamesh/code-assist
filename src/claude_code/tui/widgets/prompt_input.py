"""Multi-line prompt input widget with history and vi-mode support."""

from __future__ import annotations

from typing import ClassVar, List

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import TextArea


class PromptInput(Widget):
    """A multi-line input area that submits on Enter and inserts newlines on Shift+Enter.

    Supports command history navigation with Up/Down arrows and optional
    vi-mode keybindings.
    """

    DEFAULT_CSS = """
    PromptInput {
        height: auto;
        max-height: 10;
        dock: bottom;
        padding: 0 1;
    }

    PromptInput TextArea {
        height: auto;
        min-height: 3;
        max-height: 8;
        border: tall $primary;
    }

    PromptInput TextArea:focus {
        border: tall $secondary;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("up", "history_prev", "Previous", show=False),
        Binding("down", "history_next", "Next", show=False),
    ]

    vi_mode: reactive[bool] = reactive(False)

    def __init__(
        self,
        *,
        vi_mode: bool = False,
        id: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.vi_mode = vi_mode
        self._history: List[str] = []
        self._history_index: int = -1
        self._draft: str = ""

    # -- Compose ---------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield TextArea(id="prompt-textarea", language=None)

    def on_mount(self) -> None:
        ta = self.query_one("#prompt-textarea", TextArea)
        ta.focus()

    # -- Key handling ----------------------------------------------------------

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Track draft text while the user types."""
        if self._history_index == -1:
            self._draft = event.text_area.text

    def on_key(self, event) -> None:
        """Submit on Enter (without shift); insert newline on Shift+Enter."""
        if event.key == "enter" and not event.shift:
            event.prevent_default()
            event.stop()
            self._submit()
        # Shift+Enter falls through to default TextArea behaviour (newline).

    # -- History ---------------------------------------------------------------

    def action_history_prev(self) -> None:
        """Navigate to the previous item in command history."""
        if not self._history:
            return
        ta = self.query_one("#prompt-textarea", TextArea)

        # Only navigate history when cursor is on the first line.
        row, _col = ta.cursor_location
        if row != 0:
            return

        if self._history_index == -1:
            self._draft = ta.text
            self._history_index = len(self._history) - 1
        elif self._history_index > 0:
            self._history_index -= 1
        ta.load_text(self._history[self._history_index])

    def action_history_next(self) -> None:
        """Navigate to the next item in command history."""
        if self._history_index == -1:
            return
        ta = self.query_one("#prompt-textarea", TextArea)

        # Only navigate history when cursor is on the last line.
        row, _col = ta.cursor_location
        last_row = ta.document.line_count - 1
        if row != last_row:
            return

        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            ta.load_text(self._history[self._history_index])
        else:
            self._history_index = -1
            ta.load_text(self._draft)

    # -- Submission ------------------------------------------------------------

    def _submit(self) -> None:
        """Submit the current text and reset the input."""
        ta = self.query_one("#prompt-textarea", TextArea)
        text = ta.text.strip()
        if not text:
            return

        # Push to history.
        if not self._history or self._history[-1] != text:
            self._history.append(text)
        self._history_index = -1
        self._draft = ""

        # Clear the text area.
        ta.load_text("")

        # Notify listeners.
        self.post_message(self.Submitted(text))

    # -- Custom messages -------------------------------------------------------

    class Submitted(Message):
        """Emitted when the user submits their prompt text."""

        def __init__(self, value: str) -> None:
            super().__init__()
            self.value = value
