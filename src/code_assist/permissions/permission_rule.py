"""Permission rule matching.

Matches permission rules against tool invocations and resolves conflicts
by source priority.
"""

from __future__ import annotations

import fnmatch

from code_assist.types.permissions import (
    PermissionRule,
    PermissionRuleSource,
    PermissionRuleValue,
    ToolPermissionRulesBySource,
)

# Source priority from highest to lowest.
_SOURCE_PRIORITY: list[PermissionRuleSource] = [
    PermissionRuleSource.CLI_ARG,
    PermissionRuleSource.COMMAND,
    PermissionRuleSource.SESSION,
    PermissionRuleSource.LOCAL_SETTINGS,
    PermissionRuleSource.PROJECT_SETTINGS,
    PermissionRuleSource.FLAG_SETTINGS,
    PermissionRuleSource.POLICY_SETTINGS,
    PermissionRuleSource.USER_SETTINGS,
]


def match_rule(rule_content: str, tool_name: str, tool_input: dict) -> bool:  # noqa: ARG001
    """Return True if *rule_content* matches the given tool invocation.

    A rule content string is matched against the tool name using
    ``fnmatch``-style glob matching.  An empty or ``None``-equivalent
    rule content is treated as a wildcard that matches everything.
    """
    if not rule_content:
        # Empty content => matches all invocations of the tool
        return True
    return fnmatch.fnmatch(tool_name, rule_content)


def find_matching_rules(
    rules_by_source: ToolPermissionRulesBySource,
    tool_name: str,
    tool_input: dict,
) -> list[PermissionRule]:
    """Find all rules that match the given tool invocation.

    Returns a list of ``PermissionRule`` objects, one for each matching
    rule-content string across all sources.
    """
    matched: list[PermissionRule] = []
    for source, rule_contents in rules_by_source.items():
        for content in rule_contents:
            # Parse the rule content: may be "tool_name:pattern" or just a pattern.
            # _parse_rule_content returns None when the rule is irrelevant for
            # this tool_name, so a non-None result means the rule matched.
            rule_value = _parse_rule_content(content, tool_name)
            if rule_value is None:
                continue
            matched.append(
                PermissionRule(
                    source=source,
                    rule_value=rule_value,
                )
            )
    return matched


def get_highest_priority_rule(rules: list[PermissionRule]) -> PermissionRule | None:
    """Return the rule with the highest-priority source.

    Priority order (highest first):
        cliArg > command > session > localSettings > projectSettings
        > flagSettings > policySettings > userSettings
    """
    if not rules:
        return None

    priority_map = {src: idx for idx, src in enumerate(_SOURCE_PRIORITY)}

    return min(
        rules,
        key=lambda r: priority_map.get(r.source, len(_SOURCE_PRIORITY)),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_rule_content(raw: str, tool_name: str) -> PermissionRuleValue | None:
    """Parse a raw rule string into a PermissionRuleValue.

    Accepted formats:
        - ``"tool_name"``          -- matches the tool with no content filter
        - ``"tool_name:pattern"``  -- matches the tool with a content glob
        - ``"pattern"``            -- matches if *tool_name* matches the pattern

    Returns ``None`` if the rule does not reference *tool_name*.
    """
    if ":" in raw:
        name_part, content_part = raw.split(":", 1)
        if name_part == tool_name:
            return PermissionRuleValue(tool_name=name_part, rule_content=content_part)
        return None

    # No colon -- the raw value is the tool name or a glob for tool names
    if fnmatch.fnmatch(tool_name, raw):
        return PermissionRuleValue(tool_name=tool_name, rule_content=None)
    return None
