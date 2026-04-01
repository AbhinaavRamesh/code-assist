"""Command semantic classification.

Classifies shell commands by their operational semantics (read, write,
search, network) for permission and concurrency decisions.
"""

from __future__ import annotations

from dataclasses import dataclass

from claude_code.utils.bash.parser import extract_command_name, split_chained_commands

# ---------------------------------------------------------------------------
# Semantics dataclass
# ---------------------------------------------------------------------------


@dataclass
class CommandSemantics:
    """Semantic classification of a shell command."""

    is_read: bool = False
    is_write: bool = False
    is_search: bool = False
    is_network: bool = False


# ---------------------------------------------------------------------------
# Classification sets
# ---------------------------------------------------------------------------

_READ_COMMANDS: set[str] = {
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
    "time",
}

_WRITE_COMMANDS: set[str] = {
    "rm", "rmdir", "mv", "cp", "mkdir", "touch",
    "chmod", "chown", "chgrp",
    "dd", "mkfs", "fdisk", "parted",
    "sed", "awk",  # can be write depending on flags
    "tee",
    "truncate", "shred",
    "install",
    "ln",
    "tar", "zip", "unzip", "gzip", "gunzip", "bzip2", "xz",
    "git",  # some git ops are write
    "npm", "yarn", "pnpm", "pip", "pip3", "cargo", "go",
    "make", "cmake", "ninja",
}

_SEARCH_COMMANDS: set[str] = {
    "grep", "rg", "ag", "ack", "fzf",
    "find", "locate", "fd",
}

_NETWORK_COMMANDS: set[str] = {
    "curl", "wget", "httpie", "http",
    "ssh", "scp", "sftp", "rsync",
    "ping", "traceroute", "tracepath",
    "dig", "nslookup", "host",
    "netstat", "ss", "lsof",
    "nc", "ncat", "socat",
    "nmap",
    "git",  # can involve network
    "npm", "yarn", "pnpm", "pip", "pip3", "cargo",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def classify_command(cmd: str) -> CommandSemantics:
    """Classify a command string into semantic categories.

    For chained commands, the result is the union of all sub-commands'
    semantics (e.g., if any part is a write, is_write is True).
    """
    parts = split_chained_commands(cmd)
    result = CommandSemantics()

    for part in parts:
        name = extract_command_name(part)
        if not name:
            continue

        if name in _READ_COMMANDS:
            result.is_read = True
        if name in _WRITE_COMMANDS:
            result.is_write = True
        if name in _SEARCH_COMMANDS:
            result.is_search = True
            result.is_read = True  # search implies read
        if name in _NETWORK_COMMANDS:
            result.is_network = True

        # If command is not in any set, treat as potential write
        if (
            name not in _READ_COMMANDS
            and name not in _WRITE_COMMANDS
            and name not in _SEARCH_COMMANDS
            and name not in _NETWORK_COMMANDS
        ):
            result.is_write = True

    return result
