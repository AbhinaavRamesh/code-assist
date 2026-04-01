"""Tests for the command registry and command definitions."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from code_assist.commands.registry import (
    find_command,
    get_all_commands,
    get_enabled_commands,
    get_user_invocable_commands,
    register_command,
    reset_registry,
)
from code_assist.types.command import CommandBase, CommandType


@pytest.fixture(autouse=True)
def _clean_registry() -> Iterator[None]:
    """Reset the registry before and after each test."""
    reset_registry()
    yield
    reset_registry()


# ---------------------------------------------------------------------------
# Registry operations
# ---------------------------------------------------------------------------


class TestRegisterCommand:
    def test_register_and_retrieve(self) -> None:
        cmd = CommandBase(name="test", description="A test command")
        register_command(cmd)
        assert get_all_commands() == [cmd]

    def test_register_multiple(self) -> None:
        cmd_a = CommandBase(name="a")
        cmd_b = CommandBase(name="b")
        register_command(cmd_a)
        register_command(cmd_b)
        assert len(get_all_commands()) == 2

    def test_get_all_returns_copy(self) -> None:
        cmd = CommandBase(name="x")
        register_command(cmd)
        result = get_all_commands()
        result.clear()
        assert len(get_all_commands()) == 1


class TestFindCommand:
    def test_find_by_name(self) -> None:
        cmd = CommandBase(name="hello")
        register_command(cmd)
        assert find_command("hello") is cmd

    def test_find_by_alias(self) -> None:
        cmd = CommandBase(name="hello", aliases=["hi", "hey"])
        register_command(cmd)
        assert find_command("hi") is cmd
        assert find_command("hey") is cmd

    def test_find_not_found(self) -> None:
        register_command(CommandBase(name="foo"))
        assert find_command("bar") is None

    def test_find_empty_registry(self) -> None:
        assert find_command("anything") is None


class TestFilterCommands:
    def test_get_enabled_commands(self) -> None:
        cmd = CommandBase(name="enabled")
        register_command(cmd)
        assert get_enabled_commands() == [cmd]

    def test_get_user_invocable_excludes_hidden(self) -> None:
        visible = CommandBase(name="visible", user_invocable=True, is_hidden=False)
        hidden = CommandBase(name="hidden", user_invocable=True, is_hidden=True)
        register_command(visible)
        register_command(hidden)
        result = get_user_invocable_commands()
        assert visible in result
        assert hidden not in result

    def test_get_user_invocable_excludes_non_invocable(self) -> None:
        invocable = CommandBase(name="inv", user_invocable=True)
        internal = CommandBase(name="internal", user_invocable=False)
        register_command(invocable)
        register_command(internal)
        result = get_user_invocable_commands()
        assert invocable in result
        assert internal not in result


class TestResetRegistry:
    def test_reset_clears_all(self) -> None:
        register_command(CommandBase(name="a"))
        register_command(CommandBase(name="b"))
        reset_registry()
        assert get_all_commands() == []


# ---------------------------------------------------------------------------
# Command properties
# ---------------------------------------------------------------------------


class TestCommandProperties:
    def test_default_values(self) -> None:
        cmd = CommandBase(name="test")
        assert cmd.command_type == CommandType.LOCAL
        assert cmd.user_invocable is True
        assert cmd.is_hidden is False
        assert cmd.aliases == []
        assert cmd.is_enabled() is True
        assert cmd.user_facing_name() == "test"

    def test_prompt_type(self) -> None:
        cmd = CommandBase(name="review", command_type=CommandType.PROMPT)
        assert cmd.command_type == CommandType.PROMPT

    def test_aliases(self) -> None:
        cmd = CommandBase(name="help", aliases=["h", "?"])
        assert cmd.aliases == ["h", "?"]


# ---------------------------------------------------------------------------
# Built-in command registration (via package import)
# ---------------------------------------------------------------------------


class TestBuiltinCommands:
    """Verify that importing the commands package registers all 24 commands."""

    def test_all_builtin_commands_registered(self) -> None:
        # Import triggers registration
        import code_assist.commands  # noqa: F811

        # Re-import doesn't re-register (module cache), but we need the
        # registry populated. Since autouse fixture clears it, we re-register.
        from code_assist.commands import _ALL_COMMANDS

        for cmd in _ALL_COMMANDS:
            register_command(cmd)

        all_cmds = get_all_commands()
        assert len(all_cmds) == 24

        expected_names = {
            "help", "clear", "compact", "config", "cost", "diff",
            "doctor", "memory", "model", "resume", "review", "session",
            "status", "tasks", "theme", "vim", "commit", "permissions",
            "plan", "hooks", "mcp", "login", "logout", "version",
        }
        actual_names = {c.name for c in all_cmds}
        assert actual_names == expected_names

    def test_prompt_commands(self) -> None:
        from code_assist.commands import compact_command, commit_command, review_command

        assert compact_command.command_type == CommandType.PROMPT
        assert commit_command.command_type == CommandType.PROMPT
        assert review_command.command_type == CommandType.PROMPT

    def test_local_commands(self) -> None:
        from code_assist.commands import (
            clear_command,
            cost_command,
            doctor_command,
            help_command,
            model_command,
            version_command,
            vim_command,
        )

        for cmd in [help_command, clear_command, cost_command, doctor_command,
                     model_command, version_command, vim_command]:
            assert cmd.command_type == CommandType.LOCAL

    def test_all_user_invocable(self) -> None:
        from code_assist.commands import _ALL_COMMANDS

        for cmd in _ALL_COMMANDS:
            assert cmd.user_invocable is True, f"{cmd.name} should be user_invocable"
