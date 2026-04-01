"""Filesystem permission checks.

Validates file paths against the project root and system-protected
directories.
"""

from __future__ import annotations

import os

from claude_code.types.permissions import (
    AdditionalWorkingDirectory,
    PermissionMode,
    PermissionResult,
)

from claude_code.permissions.permission_mode import allows_writes
from claude_code.permissions.permission_result import (
    create_allow_result,
    create_deny_result,
)


# Paths that must never be written to.
SYSTEM_PATHS: set[str] = {
    "/System",
    "/bin",
    "/usr/bin",
    "/etc",
    "/sbin",
    "/usr/sbin",
}


def is_path_within_project(
    path: str,
    project_root: str,
    additional_dirs: dict[str, AdditionalWorkingDirectory] | None = None,
) -> bool:
    """Return True if *path* is inside the project root or an allowed directory."""
    resolved = os.path.realpath(path)
    resolved_root = os.path.realpath(project_root)

    if resolved.startswith(resolved_root + os.sep) or resolved == resolved_root:
        return True

    if additional_dirs:
        for dir_info in additional_dirs.values():
            resolved_dir = os.path.realpath(dir_info.path)
            if resolved.startswith(resolved_dir + os.sep) or resolved == resolved_dir:
                return True

    return False


def is_path_writable(
    path: str,
    project_root: str,
    mode: PermissionMode,
) -> PermissionResult:
    """Check whether *path* can be written in the given permission mode.

    Returns a PermissionResult: allow or deny.
    """
    if not allows_writes(mode):
        return create_deny_result("Write operations are not permitted in plan mode")

    resolved = os.path.realpath(path)

    for sys_path in SYSTEM_PATHS:
        sys_resolved = os.path.realpath(sys_path)
        if resolved.startswith(sys_resolved + os.sep) or resolved == sys_resolved:
            return create_deny_result(
                f"Cannot write to system path: {sys_path}"
            )

    if not is_path_within_project(path, project_root):
        return create_deny_result(
            f"Path is outside the project root: {path}"
        )

    return create_allow_result()
