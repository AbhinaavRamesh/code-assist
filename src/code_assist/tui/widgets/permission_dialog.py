"""Modal permission dialog for tool-use approval."""

from __future__ import annotations

from enum import Enum
from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class PermissionDecision(Enum):
    """Possible outcomes of a permission prompt."""

    ALLOW = "allow"
    DENY = "deny"
    ALWAYS_ALLOW = "always_allow"


class PermissionDialog(ModalScreen[PermissionDecision]):
    """A modal dialog that asks the user to approve or deny a tool invocation.

    Keyboard shortcuts:
    - ``y`` / ``Enter`` -- Allow
    - ``n`` / ``Escape`` -- Deny
    - ``a`` -- Always Allow (for this tool in this session)
    """

    DEFAULT_CSS = """
    PermissionDialog {
        align: center middle;
    }

    PermissionDialog #dialog-container {
        width: 70;
        max-width: 90%;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: tall $primary;
        padding: 1 2;
    }

    PermissionDialog #dialog-title {
        text-align: center;
        text-style: bold;
        color: #f59e0b;
        margin: 0 0 1 0;
    }

    PermissionDialog #tool-name {
        color: #7c3aed;
        text-style: bold;
        margin: 0 0 1 0;
    }

    PermissionDialog #tool-summary {
        color: #9ca3af;
        margin: 0 0 1 0;
        max-height: 12;
        overflow-y: auto;
    }

    PermissionDialog #button-row {
        height: 3;
        align-horizontal: center;
        margin: 1 0 0 0;
    }

    PermissionDialog Button {
        margin: 0 1;
    }

    PermissionDialog #btn-allow {
        background: #10b981;
    }

    PermissionDialog #btn-deny {
        background: #ef4444;
    }

    PermissionDialog #btn-always {
        background: #3b82f6;
    }

    PermissionDialog .hint {
        text-align: center;
        color: #6b7280;
        text-style: dim;
        margin: 1 0 0 0;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("y", "allow", "Allow", show=False),
        Binding("enter", "allow", "Allow", show=False),
        Binding("n", "deny", "Deny", show=False),
        Binding("escape", "deny", "Deny", show=False),
        Binding("a", "always_allow", "Always Allow", show=False),
    ]

    def __init__(
        self,
        tool_name: str,
        tool_input_summary: str,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._tool_name = tool_name
        self._tool_input_summary = tool_input_summary

    # -- Compose ---------------------------------------------------------------

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog-container"):
            yield Static("Permission Required", id="dialog-title")
            yield Static(f"Tool: {self._tool_name}", id="tool-name")
            yield Static(self._tool_input_summary, id="tool-summary")
            with Horizontal(id="button-row"):
                yield Button("Allow (y)", id="btn-allow", variant="success")
                yield Button("Deny (n)", id="btn-deny", variant="error")
                yield Button("Always (a)", id="btn-always", variant="primary")
            yield Static("[y] Allow  [n] Deny  [a] Always Allow", classes="hint")

    # -- Button handlers -------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_map = {
            "btn-allow": PermissionDecision.ALLOW,
            "btn-deny": PermissionDecision.DENY,
            "btn-always": PermissionDecision.ALWAYS_ALLOW,
        }
        decision = button_map.get(event.button.id)
        if decision is not None:
            self.dismiss(decision)

    # -- Key-bound actions -----------------------------------------------------

    def action_allow(self) -> None:
        self.dismiss(PermissionDecision.ALLOW)

    def action_deny(self) -> None:
        self.dismiss(PermissionDecision.DENY)

    def action_always_allow(self) -> None:
        self.dismiss(PermissionDecision.ALWAYS_ALLOW)
