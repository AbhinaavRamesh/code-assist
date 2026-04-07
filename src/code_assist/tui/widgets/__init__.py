"""TUI widget components for Claude Code."""

from code_assist.tui.widgets.message_list import MessageList
from code_assist.tui.widgets.prompt_input import PromptInput
from code_assist.tui.widgets.spinner import Spinner
from code_assist.tui.widgets.status_line import StatusLine
from code_assist.tui.widgets.permission_dialog import PermissionDialog

__all__ = [
    "MessageList",
    "PromptInput",
    "Spinner",
    "StatusLine",
    "PermissionDialog",
]
