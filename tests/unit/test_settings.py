"""Tests for settings and config management."""

import json
from pathlib import Path

import pytest

from claude_code.config.claude_md import (
    MemoryFileInfo,
    build_claude_md_context,
    get_claude_mds,
    get_large_memory_files,
    get_memory_files,
    is_memory_file_path,
)
from claude_code.config.config import (
    get_default_global_config,
    get_default_project_config,
)
from claude_code.config.settings import (
    _deep_merge,
    get_default_settings,
    load_settings_file,
    save_settings_file,
)
from claude_code.state.app_state import AppState, get_default_app_state
from claude_code.state.bootstrap import (
    BootstrapState,
    get_bootstrap_state,
    init_bootstrap_state,
    reset_bootstrap_state,
)


class TestSettings:
    def test_default_settings(self) -> None:
        settings = get_default_settings()
        assert "permissions" in settings
        assert "hooks" in settings
        assert "mcpServers" in settings

    def test_load_missing_file(self, tmp_path: Path) -> None:
        result = load_settings_file(tmp_path / "nonexistent.json")
        assert result == {}

    def test_load_valid_file(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.json"
        path.write_text('{"key": "value"}')
        result = load_settings_file(path)
        assert result == {"key": "value"}

    def test_load_invalid_json(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.json"
        path.write_text("not json!")
        result = load_settings_file(path)
        assert result == {}

    def test_save_and_load(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.json"
        save_settings_file(path, {"hello": "world"})
        result = load_settings_file(path)
        assert result == {"hello": "world"}

    def test_deep_merge(self) -> None:
        base = {"a": 1, "nested": {"x": 1, "y": 2}}
        override = {"b": 2, "nested": {"y": 3, "z": 4}}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 2, "nested": {"x": 1, "y": 3, "z": 4}}

    def test_deep_merge_override_non_dict(self) -> None:
        base = {"a": {"x": 1}}
        override = {"a": "string"}
        result = _deep_merge(base, override)
        assert result == {"a": "string"}


class TestConfig:
    def test_default_global_config(self) -> None:
        config = get_default_global_config()
        assert config["numStartups"] == 0
        assert config["theme"] == "dark"

    def test_default_project_config(self) -> None:
        config = get_default_project_config()
        assert config["allowedTools"] == []


class TestClaudeMd:
    def test_get_memory_files_empty_project(self, tmp_path: Path) -> None:
        files = get_memory_files(
            str(tmp_path), include_managed=False, include_user=False
        )
        assert files == []

    def test_get_memory_files_with_claude_md(self, tmp_path: Path) -> None:
        (tmp_path / "CLAUDE.md").write_text("# Project rules\nDo this.")
        files = get_memory_files(
            str(tmp_path), include_managed=False, include_user=False
        )
        assert len(files) == 1
        assert files[0].source == "project"
        assert "Project rules" in files[0].content

    def test_get_memory_files_with_rules_dir(self, tmp_path: Path) -> None:
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "style.md").write_text("Use snake_case.")
        (rules_dir / "testing.md").write_text("Always write tests.")
        files = get_memory_files(
            str(tmp_path), include_managed=False, include_user=False
        )
        assert len(files) == 2

    def test_get_memory_files_with_local_md(self, tmp_path: Path) -> None:
        (tmp_path / "CLAUDE.local.md").write_text("Local override.")
        files = get_memory_files(
            str(tmp_path), include_managed=False, include_user=False
        )
        assert len(files) == 1
        assert files[0].source == "local"

    def test_build_claude_md_context(self) -> None:
        files = [
            MemoryFileInfo(path="/home/.claude/CLAUDE.md", content="Global rules", source="user"),
            MemoryFileInfo(path="/proj/CLAUDE.md", content="Project rules", source="project"),
        ]
        ctx = build_claude_md_context(files)
        assert "Global rules" in ctx
        assert "Project rules" in ctx
        assert "private global instructions" in ctx

    def test_get_claude_mds(self) -> None:
        files = [
            MemoryFileInfo(path="/proj/CLAUDE.md", content="a", source="project"),
            MemoryFileInfo(path="/proj/.claude/rules/x.md", content="b", source="project"),
        ]
        claude_mds = get_claude_mds(files)
        assert len(claude_mds) == 1

    def test_get_large_memory_files(self) -> None:
        small = MemoryFileInfo(path="a.md", content="x", source="project", size=100)
        large = MemoryFileInfo(path="b.md", content="y" * 50000, source="project", size=50000)
        result = get_large_memory_files([small, large])
        assert len(result) == 1
        assert result[0].path == "b.md"

    def test_is_memory_file_path(self) -> None:
        assert is_memory_file_path("/proj/CLAUDE.md")
        assert is_memory_file_path("/proj/CLAUDE.local.md")
        assert is_memory_file_path("/proj/.claude/rules/style.md")
        assert not is_memory_file_path("/proj/README.md")


class TestAppState:
    def test_default_app_state(self) -> None:
        state = get_default_app_state()
        assert state.verbose is False
        assert state.tasks == {}
        assert state.tool_permission_context.mode == "default"

    def test_app_state_fields(self) -> None:
        state = AppState(verbose=True, main_loop_model="claude-sonnet-4-20250514")
        assert state.verbose is True
        assert state.main_loop_model == "claude-sonnet-4-20250514"


class TestBootstrapState:
    def setup_method(self) -> None:
        reset_bootstrap_state()

    def test_singleton(self) -> None:
        s1 = get_bootstrap_state()
        s2 = get_bootstrap_state()
        assert s1 is s2

    def test_init(self) -> None:
        state = init_bootstrap_state(cwd="/tmp/test", project_root="/tmp/test")
        assert state.cwd == "/tmp/test"
        assert state.project_root == "/tmp/test"
        assert state.original_cwd == "/tmp/test"

    def test_reset_turn_metrics(self) -> None:
        state = get_bootstrap_state()
        state.turn_tool_count = 5
        state.turn_hook_count = 3
        state.reset_turn_metrics()
        assert state.turn_tool_count == 0
        assert state.turn_hook_count == 0

    def test_add_cost(self) -> None:
        state = get_bootstrap_state()
        state.add_cost(0.05)
        state.add_cost(0.03)
        assert abs(state.total_cost_usd - 0.08) < 1e-10

    def test_log_error(self) -> None:
        state = get_bootstrap_state()
        state.log_error("test error")
        assert len(state.in_memory_error_log) == 1
        assert state.in_memory_error_log[0]["error"] == "test error"
