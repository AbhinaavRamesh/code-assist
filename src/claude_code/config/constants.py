"""Configuration constants and paths."""

from __future__ import annotations

import os
from pathlib import Path


# ---------------------------------------------------------------------------
# Directory Paths
# ---------------------------------------------------------------------------

def get_home_dir() -> Path:
    """Get the user's home directory."""
    return Path.home()


def get_claude_dir() -> Path:
    """Get the ~/.claude directory."""
    return get_home_dir() / ".claude"


def get_global_config_path() -> Path:
    """Get the path to the global config file."""
    return get_claude_dir() / "config.json"


def get_global_settings_path() -> Path:
    """Get the path to global settings.json."""
    return get_claude_dir() / "settings.json"


def get_project_config_dir(project_root: str) -> Path:
    """Get the .claude directory for a project."""
    return Path(project_root) / ".claude"


def get_project_settings_path(project_root: str) -> Path:
    """Get the path to project settings.json."""
    return get_project_config_dir(project_root) / "settings.json"


def get_local_settings_path(project_root: str) -> Path:
    """Get the path to local settings.json (gitignored)."""
    return get_project_config_dir(project_root) / "settings.local.json"


def get_memory_dir(project_root: str) -> Path:
    """Get the project memory directory."""
    return get_claude_dir() / "projects" / project_root.replace("/", "-").replace("\\", "-")


def get_managed_claude_rules_dir() -> Path:
    """Get the managed CLAUDE.md rules directory (/etc/claude-code/)."""
    return Path("/etc/claude-code")


def get_user_claude_rules_dir() -> Path:
    """Get the user's CLAUDE.md rules directory."""
    return get_claude_dir()


def get_sessions_dir() -> Path:
    """Get the sessions directory."""
    return get_claude_dir() / "sessions"


def get_skills_dir() -> Path:
    """Get the user skills directory."""
    return get_claude_dir() / "skills"


def get_agents_dir() -> Path:
    """Get the user agents directory."""
    return get_claude_dir() / "agents"


def get_task_output_dir() -> Path:
    """Get the task output directory."""
    return get_claude_dir() / "task-output"


# ---------------------------------------------------------------------------
# CLAUDE.md File Names
# ---------------------------------------------------------------------------

CLAUDE_MD_FILES = [
    "CLAUDE.md",
    ".claude/CLAUDE.md",
]

CLAUDE_LOCAL_MD = "CLAUDE.local.md"

CLAUDE_RULES_DIR = ".claude/rules"

MAX_MEMORY_CHARACTER_COUNT = 40_000

MEMORY_INSTRUCTION_PROMPT = (
    "Codebase and user instructions are shown below. "
    "Be sure to adhere to these instructions. "
    "IMPORTANT: These instructions OVERRIDE any default behavior "
    "and you MUST follow them exactly as written."
)

# ---------------------------------------------------------------------------
# Feature Flags
# ---------------------------------------------------------------------------


def is_feature_enabled(name: str) -> bool:
    """Check if a feature flag is enabled via environment variable."""
    return os.environ.get(f"CODE_ASSIST_{name}", "").lower() in ("1", "true")


def get_user_type() -> str:
    """Get the user type (external by default)."""
    return os.environ.get("USER_TYPE", "external")
