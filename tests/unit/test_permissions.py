"""Tests for the permissions system.

Covers: permission modes, result helpers, rule matching, filesystem checks,
shell pattern matching, denial tracking, and permission setup.
"""

from __future__ import annotations

import os

import pytest

from code_assist.permissions.denial_tracking import DenialTracker
from code_assist.permissions.filesystem import (
    SYSTEM_PATHS,
    is_path_within_project,
    is_path_writable,
)
from code_assist.permissions.permission_mode import (
    allows_tool,
    allows_writes,
    is_auto_mode,
    is_bypass_mode,
    is_plan_mode,
)
from code_assist.permissions.permission_result import (
    create_allow_result,
    create_ask_result,
    create_deny_result,
    is_allowed,
    is_denied,
)
from code_assist.permissions.permission_rule import (
    find_matching_rules,
    get_highest_priority_rule,
    match_rule,
)
from code_assist.permissions.permission_setup import (
    create_permission_context,
    extract_permission_rules,
)
from code_assist.permissions.shell_rule_matching import (
    matches_shell_pattern,
    normalize_rule_pattern,
)
from code_assist.types.permissions import (
    PermissionBehavior,
    PermissionMode,
    PermissionRule,
    PermissionRuleSource,
    PermissionRuleValue,
)


# ---------------------------------------------------------------------------
# Permission Mode Tests
# ---------------------------------------------------------------------------


class TestPermissionMode:
    def test_is_bypass_mode(self) -> None:
        assert is_bypass_mode(PermissionMode.BYPASS_PERMISSIONS) is True
        assert is_bypass_mode(PermissionMode.DEFAULT) is False
        assert is_bypass_mode(PermissionMode.AUTO) is False

    def test_is_plan_mode(self) -> None:
        assert is_plan_mode(PermissionMode.PLAN) is True
        assert is_plan_mode(PermissionMode.DEFAULT) is False

    def test_is_auto_mode(self) -> None:
        assert is_auto_mode(PermissionMode.AUTO) is True
        assert is_auto_mode(PermissionMode.DONT_ASK) is True
        assert is_auto_mode(PermissionMode.DEFAULT) is False
        assert is_auto_mode(PermissionMode.PLAN) is False

    def test_allows_writes(self) -> None:
        assert allows_writes(PermissionMode.DEFAULT) is True
        assert allows_writes(PermissionMode.AUTO) is True
        assert allows_writes(PermissionMode.BYPASS_PERMISSIONS) is True
        assert allows_writes(PermissionMode.ACCEPT_EDITS) is True
        assert allows_writes(PermissionMode.PLAN) is False

    def test_allows_tool_bypass(self) -> None:
        assert allows_tool(PermissionMode.BYPASS_PERMISSIONS, "Bash") is True
        assert allows_tool(PermissionMode.BYPASS_PERMISSIONS, "Write") is True

    def test_allows_tool_plan_mode_read_only(self) -> None:
        assert allows_tool(PermissionMode.PLAN, "Read") is True
        assert allows_tool(PermissionMode.PLAN, "Glob") is True
        assert allows_tool(PermissionMode.PLAN, "Grep") is True

    def test_allows_tool_plan_mode_blocks_writes(self) -> None:
        assert allows_tool(PermissionMode.PLAN, "Write") is False
        assert allows_tool(PermissionMode.PLAN, "Bash") is False
        assert allows_tool(PermissionMode.PLAN, "Edit") is False

    def test_allows_tool_default(self) -> None:
        assert allows_tool(PermissionMode.DEFAULT, "Bash") is True
        assert allows_tool(PermissionMode.DEFAULT, "Read") is True


# ---------------------------------------------------------------------------
# Permission Result Tests
# ---------------------------------------------------------------------------


class TestPermissionResult:
    def test_create_allow_result(self) -> None:
        result = create_allow_result()
        assert result.behavior == "allow"
        assert result.updated_input is None
        assert result.decision_reason is None

    def test_create_allow_result_with_updated_input(self) -> None:
        result = create_allow_result(updated_input={"command": "ls"})
        assert result.updated_input == {"command": "ls"}

    def test_create_deny_result(self) -> None:
        result = create_deny_result("Not allowed")
        assert result.behavior == "deny"
        assert result.message == "Not allowed"

    def test_create_ask_result(self) -> None:
        result = create_ask_result("Allow this?")
        assert result.behavior == "ask"
        assert result.message == "Allow this?"
        assert result.suggestions is None

    def test_create_ask_result_with_suggestions(self) -> None:
        result = create_ask_result("Allow?", suggestions=[])
        assert result.suggestions == []

    def test_is_allowed(self) -> None:
        assert is_allowed(create_allow_result()) is True
        assert is_allowed(create_deny_result("no")) is False
        assert is_allowed(create_ask_result("?")) is False

    def test_is_denied(self) -> None:
        assert is_denied(create_deny_result("no")) is True
        assert is_denied(create_allow_result()) is False
        assert is_denied(create_ask_result("?")) is False


# ---------------------------------------------------------------------------
# Permission Rule Tests
# ---------------------------------------------------------------------------


class TestPermissionRule:
    def test_match_rule_empty_content(self) -> None:
        assert match_rule("", "Bash", {}) is True

    def test_match_rule_exact_match(self) -> None:
        assert match_rule("Bash", "Bash", {}) is True
        assert match_rule("Bash", "Read", {}) is False

    def test_match_rule_glob(self) -> None:
        assert match_rule("Ba*", "Bash", {}) is True
        assert match_rule("Ba*", "Read", {}) is False

    def test_find_matching_rules(self) -> None:
        rules_by_source = {
            PermissionRuleSource.USER_SETTINGS: ["Bash", "Read"],
            PermissionRuleSource.CLI_ARG: ["Bash"],
        }
        matches = find_matching_rules(rules_by_source, "Bash", {})
        assert len(matches) == 2
        sources = {r.source for r in matches}
        assert PermissionRuleSource.USER_SETTINGS in sources
        assert PermissionRuleSource.CLI_ARG in sources

    def test_find_matching_rules_none_match(self) -> None:
        rules_by_source = {
            PermissionRuleSource.USER_SETTINGS: ["Write"],
        }
        matches = find_matching_rules(rules_by_source, "Bash", {})
        assert len(matches) == 0

    def test_find_matching_rules_with_content_pattern(self) -> None:
        rules_by_source = {
            PermissionRuleSource.SESSION: ["Bash:ls *"],
        }
        matches = find_matching_rules(rules_by_source, "Bash", {"command": "ls -la"})
        assert len(matches) == 1
        assert matches[0].rule_value.rule_content == "ls *"

    def test_get_highest_priority_rule_empty(self) -> None:
        assert get_highest_priority_rule([]) is None

    def test_get_highest_priority_rule_single(self) -> None:
        rule = PermissionRule(source=PermissionRuleSource.USER_SETTINGS)
        assert get_highest_priority_rule([rule]) is rule

    def test_get_highest_priority_rule_cli_wins(self) -> None:
        user_rule = PermissionRule(
            source=PermissionRuleSource.USER_SETTINGS,
            rule_behavior=PermissionBehavior.DENY,
        )
        cli_rule = PermissionRule(
            source=PermissionRuleSource.CLI_ARG,
            rule_behavior=PermissionBehavior.ALLOW,
        )
        project_rule = PermissionRule(
            source=PermissionRuleSource.PROJECT_SETTINGS,
            rule_behavior=PermissionBehavior.ASK,
        )
        winner = get_highest_priority_rule([user_rule, cli_rule, project_rule])
        assert winner is cli_rule

    def test_get_highest_priority_local_over_project(self) -> None:
        local = PermissionRule(source=PermissionRuleSource.LOCAL_SETTINGS)
        project = PermissionRule(source=PermissionRuleSource.PROJECT_SETTINGS)
        assert get_highest_priority_rule([project, local]) is local


# ---------------------------------------------------------------------------
# Filesystem Tests
# ---------------------------------------------------------------------------


class TestFilesystem:
    def test_system_paths_populated(self) -> None:
        assert "/System" in SYSTEM_PATHS
        assert "/bin" in SYSTEM_PATHS
        assert "/usr/bin" in SYSTEM_PATHS
        assert "/etc" in SYSTEM_PATHS

    def test_is_path_within_project(self, tmp_project: str) -> None:
        inside = os.path.join(tmp_project, "src", "main.py")
        assert is_path_within_project(inside, tmp_project) is True

    def test_is_path_within_project_root_itself(self, tmp_project: str) -> None:
        assert is_path_within_project(tmp_project, tmp_project) is True

    def test_is_path_outside_project(self, tmp_project: str) -> None:
        outside = "/tmp/other/file.txt"
        assert is_path_within_project(outside, tmp_project) is False

    def test_is_path_within_additional_dirs(self, tmp_project: str) -> None:
        from code_assist.types.permissions import AdditionalWorkingDirectory

        extra_dir = "/tmp/extra-working-dir"
        additional = {
            extra_dir: AdditionalWorkingDirectory(path=extra_dir),
        }
        inside_extra = os.path.join(extra_dir, "file.py")
        assert is_path_within_project(inside_extra, tmp_project, additional) is True

    def test_is_path_writable_plan_mode(self, tmp_project: str) -> None:
        path = os.path.join(tmp_project, "test.py")
        result = is_path_writable(path, tmp_project, PermissionMode.PLAN)
        assert is_denied(result) is True

    def test_is_path_writable_system_path(self, tmp_project: str) -> None:
        result = is_path_writable("/etc/passwd", tmp_project, PermissionMode.DEFAULT)
        assert is_denied(result) is True

    def test_is_path_writable_outside_project(self, tmp_project: str) -> None:
        result = is_path_writable("/tmp/random/file.txt", tmp_project, PermissionMode.DEFAULT)
        assert is_denied(result) is True

    def test_is_path_writable_inside_project(self, tmp_project: str) -> None:
        path = os.path.join(tmp_project, "src", "app.py")
        result = is_path_writable(path, tmp_project, PermissionMode.DEFAULT)
        assert is_allowed(result) is True


# ---------------------------------------------------------------------------
# Shell Rule Matching Tests
# ---------------------------------------------------------------------------


class TestShellRuleMatching:
    def test_normalize_rule_pattern_strips_whitespace(self) -> None:
        assert normalize_rule_pattern("  ls -la  ") == "ls -la"

    def test_normalize_rule_pattern_collapses_spaces(self) -> None:
        assert normalize_rule_pattern("ls   -la") == "ls -la"

    def test_normalize_rule_pattern_removes_trailing_semicolon(self) -> None:
        assert normalize_rule_pattern("ls -la;") == "ls -la"

    def test_normalize_preserves_meaningful_content(self) -> None:
        assert normalize_rule_pattern("git commit -m 'msg'") == "git commit -m 'msg'"

    def test_matches_shell_pattern_exact(self) -> None:
        assert matches_shell_pattern("ls -la", "ls -la") is True

    def test_matches_shell_pattern_glob_star(self) -> None:
        assert matches_shell_pattern("git *", "git status") is True
        assert matches_shell_pattern("git *", "git commit -m 'test'") is True

    def test_matches_shell_pattern_no_match(self) -> None:
        assert matches_shell_pattern("git *", "npm install") is False

    def test_matches_shell_pattern_wildcard_all(self) -> None:
        assert matches_shell_pattern("*", "anything goes") is True

    def test_matches_shell_pattern_empty_pattern(self) -> None:
        assert matches_shell_pattern("", "ls") is False

    def test_matches_shell_pattern_question_mark(self) -> None:
        assert matches_shell_pattern("l?", "ls") is True
        assert matches_shell_pattern("l?", "ll") is True
        assert matches_shell_pattern("l?", "lss") is False

    def test_matches_shell_pattern_normalizes_both(self) -> None:
        assert matches_shell_pattern("  git  *  ", "  git   status  ") is True


# ---------------------------------------------------------------------------
# Denial Tracking Tests
# ---------------------------------------------------------------------------


class TestDenialTracker:
    def test_initial_state(self) -> None:
        tracker = DenialTracker()
        assert tracker.get_consecutive_denials() == 0
        assert tracker.should_escalate() is False
        assert tracker.last_tool is None

    def test_record_denial(self) -> None:
        tracker = DenialTracker()
        tracker.record_denial("Bash")
        assert tracker.get_consecutive_denials() == 1
        assert tracker.last_tool == "Bash"

    def test_multiple_denials(self) -> None:
        tracker = DenialTracker()
        tracker.record_denial("Bash")
        tracker.record_denial("Write")
        assert tracker.get_consecutive_denials() == 2
        assert tracker.last_tool == "Write"

    def test_escalation_threshold(self) -> None:
        tracker = DenialTracker()
        tracker.record_denial("Bash")
        tracker.record_denial("Bash")
        assert tracker.should_escalate() is False
        tracker.record_denial("Bash")
        assert tracker.should_escalate() is True

    def test_escalation_above_threshold(self) -> None:
        tracker = DenialTracker()
        for _ in range(5):
            tracker.record_denial("Bash")
        assert tracker.should_escalate() is True
        assert tracker.get_consecutive_denials() == 5

    def test_reset(self) -> None:
        tracker = DenialTracker()
        for _ in range(4):
            tracker.record_denial("Bash")
        tracker.reset()
        assert tracker.get_consecutive_denials() == 0
        assert tracker.should_escalate() is False
        assert tracker.last_tool is None


# ---------------------------------------------------------------------------
# Permission Setup Tests
# ---------------------------------------------------------------------------


class TestPermissionSetup:
    def test_extract_permission_rules_empty(self) -> None:
        allow, deny, ask = extract_permission_rules({})
        assert allow == {}
        assert deny == {}
        assert ask == {}

    def test_extract_permission_rules_populated(self) -> None:
        settings = {
            "permissions": {
                "allow": {
                    "userSettings": ["Bash", "Read"],
                    "cliArg": ["Write"],
                },
                "deny": {
                    "projectSettings": ["Bash:rm *"],
                },
                "ask": {},
            }
        }
        allow, deny, ask = extract_permission_rules(settings)
        assert PermissionRuleSource.USER_SETTINGS in allow
        assert allow[PermissionRuleSource.USER_SETTINGS] == ["Bash", "Read"]
        assert allow[PermissionRuleSource.CLI_ARG] == ["Write"]
        assert PermissionRuleSource.PROJECT_SETTINGS in deny
        assert deny[PermissionRuleSource.PROJECT_SETTINGS] == ["Bash:rm *"]
        assert ask == {}

    def test_extract_ignores_invalid_sources(self) -> None:
        settings = {
            "permissions": {
                "allow": {
                    "invalidSource": ["Bash"],
                    "userSettings": ["Read"],
                },
            }
        }
        allow, _, _ = extract_permission_rules(settings)
        assert PermissionRuleSource.USER_SETTINGS in allow
        assert len(allow) == 1  # invalidSource was skipped

    def test_create_permission_context(self) -> None:
        settings = {
            "permissions": {
                "allow": {
                    "userSettings": ["Bash"],
                },
                "deny": {},
                "ask": {},
            },
            "is_bypass_permissions_mode_available": True,
        }
        ctx = create_permission_context(settings, PermissionMode.AUTO, "/project")
        assert ctx.mode == PermissionMode.AUTO
        assert PermissionRuleSource.USER_SETTINGS in ctx.always_allow_rules
        assert ctx.is_bypass_permissions_mode_available is True

    def test_create_permission_context_defaults(self) -> None:
        ctx = create_permission_context({}, PermissionMode.DEFAULT, "/project")
        assert ctx.mode == PermissionMode.DEFAULT
        assert ctx.always_allow_rules == {}
        assert ctx.always_deny_rules == {}
        assert ctx.always_ask_rules == {}
        assert ctx.is_bypass_permissions_mode_available is False
