"""Command safety analysis.

Detects dangerous patterns in shell commands to prevent accidental
or malicious system damage.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class CommandSafetyResult:
    """Result of analyzing a command for safety."""

    is_safe: bool
    reason: str
    risk_level: str  # "low", "medium", "high", "critical"


# Each tuple is (compiled regex pattern, human-readable reason).
# Patterns are checked against the raw command string.
DANGEROUS_PATTERNS: list[tuple[str, str]] = [
    # Recursive forced deletion of root or system paths
    (r"rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+)?-[a-zA-Z]*r[a-zA-Z]*\s+/\s*$", "Recursive deletion of root filesystem"),
    (r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)?-[a-zA-Z]*f[a-zA-Z]*\s+/\s*$", "Recursive forced deletion of root filesystem"),
    (r"rm\s+-rf\s+/(?:\s|$)", "Recursive forced deletion of root filesystem"),
    (r"rm\s+-rf\s+/\*", "Recursive forced deletion of all root contents"),
    # dd to disk devices
    (r"dd\s+.*if=.*of=/dev/[sh]d[a-z]", "Direct disk write via dd"),
    (r"dd\s+.*of=/dev/[sh]d[a-z]", "Direct disk write via dd"),
    # Fork bomb
    (r":\(\)\s*\{\s*:\|:&\s*\}\s*;:", "Fork bomb"),
    (r"\.\/fork_bomb", "Fork bomb script"),
    # Overwrite system devices
    (r">\s*/dev/sd[a-z]", "Overwrite disk device"),
    (r">\s*/dev/nvme", "Overwrite NVMe device"),
    # Dangerous redirects to system files
    (r">\s*/etc/passwd", "Overwrite passwd file"),
    (r">\s*/etc/shadow", "Overwrite shadow file"),
    (r">\s*/etc/sudoers", "Overwrite sudoers file"),
    # Sudo usage
    (r"\bsudo\b", "Elevated privileges via sudo"),
    # chmod 777 on system dirs
    (r"chmod\s+777\s+/", "Setting world-writable permissions on system path"),
    (r"chmod\s+-R\s+777", "Recursively setting world-writable permissions"),
    # Curl/wget piped to shell
    (r"curl\s.*\|\s*(?:ba)?sh", "Piping remote script to shell"),
    (r"wget\s.*\|\s*(?:ba)?sh", "Piping remote script to shell"),
    (r"curl\s.*\|\s*sudo", "Piping remote content to sudo"),
    # Python/perl one-liners that could be dangerous
    (r"python[23]?\s+-c\s+.*__import__.*os.*system", "Python system command execution"),
    # mkfs on devices
    (r"mkfs", "Filesystem formatting"),
    # Overwriting MBR
    (r"dd\s+.*of=/dev/[sh]d[a-z]\s+.*bs=512\s+.*count=1", "Overwriting disk boot sector"),
    # Environment manipulation that could be dangerous
    (r"export\s+PATH\s*=\s*$", "Clearing PATH variable"),
    (r"unset\s+PATH", "Unsetting PATH variable"),
    # History manipulation
    (r"history\s+-c", "Clearing shell history"),
    # Crontab removal
    (r"crontab\s+-r", "Removing all cron jobs"),
]

# Pre-compile for performance
_COMPILED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(pattern), reason) for pattern, reason in DANGEROUS_PATTERNS
]


def analyze_command_safety(cmd: str) -> CommandSafetyResult:
    """Analyze a shell command for dangerous patterns.

    Returns a CommandSafetyResult indicating whether the command is safe,
    a human-readable reason if not, and a risk level.
    """
    cmd_stripped = cmd.strip()

    if not cmd_stripped:
        return CommandSafetyResult(is_safe=True, reason="Empty command", risk_level="low")

    # Check against all dangerous patterns
    for pattern, reason in _COMPILED_PATTERNS:
        if pattern.search(cmd_stripped):
            # Determine risk level based on the reason
            risk = _classify_risk(reason)
            return CommandSafetyResult(
                is_safe=False,
                reason=reason,
                risk_level=risk,
            )

    return CommandSafetyResult(
        is_safe=True,
        reason="No dangerous patterns detected",
        risk_level="low",
    )


def _classify_risk(reason: str) -> str:
    """Classify risk level based on the matched reason."""
    critical_keywords = [
        "root filesystem",
        "disk write",
        "fork bomb",
        "boot sector",
        "disk device",
        "NVMe device",
        "passwd",
        "shadow",
        "sudoers",
        "formatting",
    ]
    high_keywords = [
        "sudo",
        "world-writable",
        "remote script",
        "clearing PATH",
        "unsetting PATH",
    ]

    reason_lower = reason.lower()
    for keyword in critical_keywords:
        if keyword.lower() in reason_lower:
            return "critical"
    for keyword in high_keywords:
        if keyword.lower() in reason_lower:
            return "high"
    return "medium"
