"""Read-only command validation.

Determines whether a shell command will only read data and not
modify any files or system state.
"""

from __future__ import annotations

import re

from claude_code.tools.bash.sed_parser import is_sed_edit
from claude_code.utils.bash.parser import (
    extract_command_name,
    parse_command,
    split_chained_commands,
)

# Commands that are always read-only regardless of flags
_ALWAYS_READ_ONLY: set[str] = {
    "cat", "head", "tail", "less", "more", "bat",
    "ls", "dir", "stat", "file", "wc", "du", "df",
    "tree", "realpath", "basename", "dirname",
    "echo", "printf", "pwd", "date", "cal", "uptime",
    "whoami", "id", "groups", "hostname", "uname", "arch",
    "nproc", "free", "lscpu", "lsblk",
    "env", "printenv", "locale", "which", "whereis", "type",
    "man", "help", "info",
    "test", "true", "false",
    "bc", "expr", "seq",
    "md5sum", "sha256sum", "sha1sum", "b2sum", "cksum", "base64",
    "sort", "uniq", "cut", "tr", "diff", "comm", "paste",
    "column", "fmt", "fold", "expand", "unexpand", "nl", "rev", "tac",
    "strings", "hexdump", "xxd", "od", "jq", "yq", "xq",
    "grep", "rg", "ag", "ack", "fzf",
    "find", "locate", "fd",
    "time",
    "sleep",
    "wait",
}

# Git subcommands that are read-only
_GIT_READ_ONLY_SUBCOMMANDS: set[str] = {
    "status", "log", "diff", "show", "branch", "tag",
    "describe", "shortlog", "rev-parse", "rev-list",
    "ls-files", "ls-tree", "ls-remote",
    "blame", "annotate", "grep",
    "config",  # when used for reading
    "remote",  # when listing
    "stash", "reflog",
}


def validate_read_only(cmd: str) -> bool:
    """Check if a command is truly read-only.

    Inspects all sub-commands in chained commands. Returns True only if
    every sub-command is determined to be read-only.
    """
    parts = split_chained_commands(cmd)
    if not parts:
        return True  # empty command is trivially read-only

    return all(_is_single_command_read_only(part) for part in parts)


def _is_single_command_read_only(cmd: str) -> bool:
    """Check if a single (non-chained) command is read-only."""
    name = extract_command_name(cmd)
    if not name:
        return True  # empty

    # Output redirection always makes a command non-read-only,
    # regardless of what the base command is.
    if _has_output_redirect(cmd):
        return False

    # Always read-only commands (when no redirect)
    if name in _ALWAYS_READ_ONLY:
        return True

    # Git: check subcommand
    if name == "git":
        return _is_git_read_only(cmd)

    # sed: check for -i flag
    if name == "sed":
        return not is_sed_edit(cmd)

    # awk: read-only unless redirecting output via > in the command
    if name == "awk":
        return not _has_output_redirect(cmd)

    return False  # unknown commands are assumed not read-only


def _is_git_read_only(cmd: str) -> bool:
    """Check if a git command is read-only based on subcommand."""
    parts = parse_command(cmd)
    # Find the git subcommand (skip 'git' and any flags like -C)
    for i, part in enumerate(parts):
        if i == 0:
            continue  # skip 'git' itself
        if part.startswith("-"):
            continue  # skip flags
        return part in _GIT_READ_ONLY_SUBCOMMANDS
    return False


def _has_output_redirect(cmd: str) -> bool:
    """Check if a command contains output redirection (> or >>).

    Ignores redirections inside quotes.
    """
    in_single = False
    in_double = False
    escaped = False

    for i, ch in enumerate(cmd):
        if escaped:
            escaped = False
            continue
        if ch == "\\" and not in_single:
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            continue
        if in_single or in_double:
            continue

        # Check for > but not inside a file descriptor redirect that reads (e.g., <)
        if ch == ">" and (i == 0 or cmd[i - 1] != "<"):
            return True

    return False
