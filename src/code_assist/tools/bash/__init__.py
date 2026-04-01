"""Bash tool package.

Provides shell command execution with safety analysis, permission
checks, and sandbox support.
"""

from code_assist.tools.bash.bash_tool import BashInput, BashTool
from code_assist.tools.bash.command_semantics import CommandSemantics, classify_command
from code_assist.tools.bash.security import CommandSafetyResult, analyze_command_safety

__all__ = [
    "BashInput",
    "BashTool",
    "CommandSafetyResult",
    "CommandSemantics",
    "analyze_command_safety",
    "classify_command",
]
