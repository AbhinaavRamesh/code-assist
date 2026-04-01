"""Permission context construction from settings.

Builds a ``ToolPermissionContext`` from a settings dictionary and
extracts categorised permission rules.
"""

from __future__ import annotations

from code_assist.types.permissions import (
    PermissionBehavior,
    PermissionMode,
    PermissionRuleSource,
    ToolPermissionContext,
    ToolPermissionRulesBySource,
)


def extract_permission_rules(
    settings: dict,
) -> tuple[ToolPermissionRulesBySource, ToolPermissionRulesBySource, ToolPermissionRulesBySource]:
    """Extract permission rules from a settings dictionary.

    The settings dict is expected to have an optional ``"permissions"``
    key containing ``"allow"``, ``"deny"``, and ``"ask"`` sub-dicts,
    each mapping a ``PermissionRuleSource`` value to a list of rule
    strings.

    Returns:
        A 3-tuple of ``(allow_rules, deny_rules, ask_rules)``.
    """
    perms = settings.get("permissions", {})

    allow_rules: ToolPermissionRulesBySource = {}
    deny_rules: ToolPermissionRulesBySource = {}
    ask_rules: ToolPermissionRulesBySource = {}

    for behavior_key, target in (
        (PermissionBehavior.ALLOW, allow_rules),
        (PermissionBehavior.DENY, deny_rules),
        (PermissionBehavior.ASK, ask_rules),
    ):
        section = perms.get(behavior_key, perms.get(str(behavior_key), {}))
        if isinstance(section, dict):
            for source_str, rule_list in section.items():
                try:
                    source = PermissionRuleSource(source_str)
                except ValueError:
                    continue
                if isinstance(rule_list, list):
                    target[source] = list(rule_list)

    return allow_rules, deny_rules, ask_rules


def create_permission_context(
    settings: dict,
    mode: PermissionMode,
    project_root: str,  # noqa: ARG001
) -> ToolPermissionContext:
    """Build a ``ToolPermissionContext`` from a settings dict and mode.

    Args:
        settings: Application settings dictionary.
        mode: The active permission mode.
        project_root: Absolute path to the project root (reserved for
            future directory-based rules).

    Returns:
        A fully populated ``ToolPermissionContext``.
    """
    allow_rules, deny_rules, ask_rules = extract_permission_rules(settings)

    return ToolPermissionContext(
        mode=mode,
        always_allow_rules=allow_rules,
        always_deny_rules=deny_rules,
        always_ask_rules=ask_rules,
        is_bypass_permissions_mode_available=settings.get(
            "is_bypass_permissions_mode_available", False
        ),
        is_auto_mode_available=settings.get("is_auto_mode_available"),
        should_avoid_permission_prompts=settings.get("should_avoid_permission_prompts"),
    )
