"""TUI widget components for Claude Code."""

from claude_code.tui.widgets.message_list import MessageList
from claude_code.tui.widgets.prompt_input import PromptInput
from claude_code.tui.widgets.spinner import Spinner
from claude_code.tui.widgets.status_line import StatusLine
from claude_code.tui.widgets.permission_dialog import PermissionDialog

__all__ = [
    "MessageList",
    "PromptInput",
    "Spinner",
    "StatusLine",
    "PermissionDialog",
]
