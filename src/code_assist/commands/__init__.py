"""Slash commands package - registers all built-in commands on import."""

from code_assist.commands.clear import clear_command
from code_assist.commands.commit import commit_command
from code_assist.commands.compact import compact_command
from code_assist.commands.config_cmd import config_command
from code_assist.commands.cost import cost_command
from code_assist.commands.diff import diff_command
from code_assist.commands.doctor import doctor_command
from code_assist.commands.help import help_command
from code_assist.commands.hooks_cmd import hooks_command
from code_assist.commands.login import login_command
from code_assist.commands.logout import logout_command
from code_assist.commands.mcp_cmd import mcp_command
from code_assist.commands.memory_cmd import memory_command
from code_assist.commands.model import model_command
from code_assist.commands.permissions_cmd import permissions_command
from code_assist.commands.plan import plan_command
from code_assist.commands.registry import register_command
from code_assist.commands.resume import resume_command
from code_assist.commands.review import review_command
from code_assist.commands.session import session_command
from code_assist.commands.status import status_command
from code_assist.commands.tasks_cmd import tasks_command
from code_assist.commands.theme import theme_command
from code_assist.commands.version import version_command
from code_assist.commands.vim import vim_command

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
