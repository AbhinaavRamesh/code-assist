"""Known command classifications.

Categorizes shell commands by safety level for permission decisions.
"""

from __future__ import annotations

from claude_code.utils.bash.parser import extract_command_name, split_chained_commands

# ---------------------------------------------------------------------------
# Command sets
# ---------------------------------------------------------------------------

KNOWN_SAFE_COMMANDS: set[str] = {
    # File listing / inspection
    "ls",
    "dir",
    "stat",
    "file",
    "wc",
    "du",
    "df",
    "find",
    "tree",
    "realpath",
    "basename",
    "dirname",
    # Reading
    "cat",
    "head",
    "tail",
    "less",
    "more",
    "bat",
    # Search
    "grep",
    "rg",
    "ag",
    "ack",
    "fzf",
    # Text processing (read-only)
    "sort",
    "uniq",
    "cut",
    "tr",
    "diff",
    "comm",
    "paste",
    "column",
    "fmt",
    "fold",
    "expand",
    "unexpand",
    "nl",
    "rev",
    "tac",
    "strings",
    "hexdump",
    "xxd",
    "od",
    "jq",
    "yq",
    "xq",
    # Output / info
    "echo",
    "printf",
    "pwd",
    "date",
    "cal",
    "uptime",
    "whoami",
    "id",
    "groups",
    "hostname",
    "uname",
    "arch",
    "nproc",
    "free",
    "lscpu",
    "lsblk",
    "lsusb",
    "lspci",
    # Environment
    "env",
    "printenv",
    "locale",
    "which",
    "whereis",
    "type",
    "command",
    "hash",
    # Version / help
    "man",
    "help",
    "info",
    # Git (read-only)
    "git",
    # Testing
    "test",
    "true",
    "false",
    # Math
    "bc",
    "expr",
    "seq",
    # Misc safe
    "tee",
    "xargs",
    "time",
    "timeout",
    "yes",
    "sleep",
    "wait",
    "md5sum",
    "sha256sum",
    "sha1sum",
    "b2sum",
    "cksum",
    "base64",
}

DESTRUCTIVE_COMMANDS: set[str] = {
    # File removal / overwriting
    "rm",
    "rmdir",
    "shred",
    "truncate",
    # Disk / filesystem
    "dd",
    "mkfs",
    "fdisk",
    "parted",
    "format",
    "mount",
    "umount",
    # System modification
    "reboot",
    "shutdown",
    "halt",
    "poweroff",
    "init",
    "systemctl",
    # Package managers (can modify system)
    "apt",
    "apt-get",
    "yum",
    "dnf",
    "pacman",
    "brew",
    "snap",
    "flatpak",
    # Network destructive
    "iptables",
    "ip6tables",
    "nft",
    "ifconfig",
    "route",
    # User / permission
    "useradd",
    "userdel",
    "usermod",
    "groupadd",
    "groupdel",
    "passwd",
    "chpasswd",
    # Dangerous utilities
    "kill",
    "killall",
    "pkill",
}


def is_known_safe(cmd: str) -> bool:
    """Check if all commands in a (possibly chained) command are known safe.

    Returns False if any sub-command is not in KNOWN_SAFE_COMMANDS.
    """
    parts = split_chained_commands(cmd)
    if not parts:
        return False

    for part in parts:
        name = extract_command_name(part)
        if not name or name not in KNOWN_SAFE_COMMANDS:
            return False
    return True


def is_potentially_destructive(cmd: str) -> bool:
    """Check if any command in a (possibly chained) command is destructive.

    Returns True if any sub-command's base name is in DESTRUCTIVE_COMMANDS.
    """
    parts = split_chained_commands(cmd)
    for part in parts:
        name = extract_command_name(part)
        if name in DESTRUCTIVE_COMMANDS:
            return True
    return False
