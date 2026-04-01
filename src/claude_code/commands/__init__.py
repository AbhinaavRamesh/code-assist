"""Slash commands package - registers all built-in commands on import."""

from claude_code.commands.clear import clear_command
from claude_code.commands.commit import commit_command
from claude_code.commands.compact import compact_command
from claude_code.commands.config_cmd import config_command
from claude_code.commands.cost import cost_command
from claude_code.commands.diff import diff_command
from claude_code.commands.doctor import doctor_command
from claude_code.commands.help import help_command
from claude_code.commands.hooks_cmd import hooks_command
from claude_code.commands.login import login_command
from claude_code.commands.logout import logout_command
from claude_code.commands.mcp_cmd import mcp_command
from claude_code.commands.memory_cmd import memory_command
from claude_code.commands.model import model_command
from claude_code.commands.permissions_cmd import permissions_command
from claude_code.commands.plan import plan_command
from claude_code.commands.registry import register_command
from claude_code.commands.resume import resume_command
from claude_code.commands.review import review_command
from claude_code.commands.session import session_command
from claude_code.commands.status import status_command
from claude_code.commands.tasks_cmd import tasks_command
from claude_code.commands.theme import theme_command
from claude_code.commands.version import version_command
from claude_code.commands.vim import vim_command

_ALL_COMMANDS = [
    help_command,
    clear_command,
    compact_command,
    config_command,
    cost_command,
    diff_command,
    doctor_command,
    memory_command,
    model_command,
    resume_command,
    review_command,
    session_command,
    status_command,
    tasks_command,
    theme_command,
    vim_command,
    commit_command,
    permissions_command,
    plan_command,
    hooks_command,
    mcp_command,
    login_command,
    logout_command,
    version_command,
]

for _cmd in _ALL_COMMANDS:
    register_command(_cmd)

__all__ = [
    "clear_command",
    "commit_command",
    "compact_command",
    "config_command",
    "cost_command",
    "diff_command",
    "doctor_command",
    "help_command",
    "hooks_command",
    "login_command",
    "logout_command",
    "mcp_command",
    "memory_command",
    "model_command",
    "permissions_command",
    "plan_command",
    "register_command",
    "resume_command",
    "review_command",
    "session_command",
    "status_command",
    "tasks_command",
    "theme_command",
    "version_command",
    "vim_command",
]
