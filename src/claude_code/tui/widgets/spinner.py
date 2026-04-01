"""Animated activity spinner widget with status text."""

from __future__ import annotations

from typing import ClassVar, Literal

from textual.reactive import reactive
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Static

SpinnerMode = Literal["thinking", "tool_use", "streaming"]

# Braille spinner frames for a smooth animation.
_BRAILLE_FRAMES: list[str] = [
    "\u2801", "\u2803", "\u2807", "\u280f",
    "\u281f", "\u283f", "\u287f", "\u28ff",
    "\u28fe", "\u28fc", "\u28f8", "\u28f0",
    "\u28e0", "\u28c0", "\u2880", "\u2800",
]

_DOTS_FRAMES: list[str] = ["   ", ".  ", ".. ", "..."]

_MODE_LABELS: dict[SpinnerMode, str] = {
    "thinking": "Thinking",
    "tool_use": "Running tool",
    "streaming": "Streaming",
}


class Spinner(Widget):
    """Animated spinner with a configurable mode and optional status text.

    Modes control the default label:
    - ``thinking`` -- general model processing
    - ``tool_use`` -- a tool is being executed
    - ``streaming`` -- response tokens are arriving
    """

    DEFAULT_CSS = """
    Spinner {
        height: 1;
        padding: 0 1;
        color: #7c3aed;
    }

    Spinner .spinner-frame {
        width: 4;
    }

    Spinner .spinner-text {
        width: 1fr;
        color: #9ca3af;
    }
    """

    mode: reactive[SpinnerMode] = reactive("thinking")
    status_text: reactive[str] = reactive("")

    _frame_index: int = 0
    _timer: Timer | None = None

    def compose(self):
        yield Static("", classes="spinner-frame", id="spinner-frame")
        yield Static("", classes="spinner-text", id="spinner-text")

    def on_mount(self) -> None:
        self._timer = self.set_interval(1 / 12, self._advance_frame)

    def on_unmount(self) -> None:
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    # -- Reactives -------------------------------------------------------------

    def watch_mode(self, new_mode: SpinnerMode) -> None:
        self._update_text()

    def watch_status_text(self, new_text: str) -> None:
        self._update_text()

    # -- Internal --------------------------------------------------------------

    def _advance_frame(self) -> None:
        """Cycle to the next animation frame."""
        if not self.visible:
            return
        frames = _BRAILLE_FRAMES
        self._frame_index = (self._frame_index + 1) % len(frames)
        try:
            self.query_one("#spinner-frame", Static).update(frames[self._frame_index])
        except Exception:
            pass

    def _update_text(self) -> None:
        """Refresh the status label beside the spinner."""
        label = _MODE_LABELS.get(self.mode, "Working")
        if self.status_text:
            label = f"{label}: {self.status_text}"
        label += " ..."
        try:
            self.query_one("#spinner-text", Static).update(label)
        except Exception:
            pass
