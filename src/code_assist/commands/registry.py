"""Command registry - loading, discovery, and lookup."""

from __future__ import annotations

from code_assist.types.command import CommandBase

_registered_commands: list[CommandBase] = []


def register_command(cmd: CommandBase) -> None:
    """Register a command in the global registry."""
    _registered_commands.append(cmd)


def get_all_commands() -> list[CommandBase]:
    """Return a copy of all registered commands."""
    return list(_registered_commands)


def find_command(name: str) -> CommandBase | None:
    """Find a command by name or alias."""
    for cmd in _registered_commands:
        if cmd.name == name or name in cmd.aliases:
            return cmd
    return None


def get_enabled_commands() -> list[CommandBase]:
    """Return all currently enabled commands."""
    return [c for c in _registered_commands if c.is_enabled()]


def get_user_invocable_commands() -> list[CommandBase]:
    """Return enabled commands that users can invoke and are not hidden."""
    return [c for c in get_enabled_commands() if c.user_invocable and not c.is_hidden]


def reset_registry() -> None:
    """Clear all registered commands (useful for testing)."""
    _registered_commands.clear()
