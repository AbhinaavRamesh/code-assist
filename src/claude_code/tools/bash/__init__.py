"""Bash tool package.

Provides shell command execution with safety analysis, permission
checks, and sandbox support.
"""

from claude_code.tools.bash.bash_tool import BashInput, BashTool
from claude_code.tools.bash.command_semantics import CommandSemantics, classify_command
from claude_code.tools.bash.security import CommandSafetyResult, analyze_command_safety

__all__ = [
    "BashInput",
    "BashTool",
    "CommandSafetyResult",
    "CommandSemantics",
    "analyze_command_safety",
    "classify_command",
]
