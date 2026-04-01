"""Permission system types.

Permission system types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal


# ---------------------------------------------------------------------------
# Permission Modes
# ---------------------------------------------------------------------------

EXTERNAL_PERMISSION_MODES = (
    "acceptEdits",
    "bypassPermissions",
    "default",
    "dontAsk",
    "plan",
)


class PermissionMode(StrEnum):
    ACCEPT_EDITS = "acceptEdits"
    BYPASS_PERMISSIONS = "bypassPermissions"
    DEFAULT = "default"
    DONT_ASK = "dontAsk"
    PLAN = "plan"
    AUTO = "auto"
    BUBBLE = "bubble"


ExternalPermissionMode = Literal[
    "acceptEdits", "bypassPermissions", "default", "dontAsk", "plan"
]


# ---------------------------------------------------------------------------
# Permission Behaviors
# ---------------------------------------------------------------------------


class PermissionBehavior(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


# ---------------------------------------------------------------------------
# Permission Rules
# ---------------------------------------------------------------------------


class PermissionRuleSource(StrEnum):
    USER_SETTINGS = "userSettings"
    PROJECT_SETTINGS = "projectSettings"
    LOCAL_SETTINGS = "localSettings"
    FLAG_SETTINGS = "flagSettings"
    POLICY_SETTINGS = "policySettings"
    CLI_ARG = "cliArg"
    COMMAND = "command"
    SESSION = "session"


class PermissionUpdateDestination(StrEnum):
    USER_SETTINGS = "userSettings"
    PROJECT_SETTINGS = "projectSettings"
    LOCAL_SETTINGS = "localSettings"
    SESSION = "session"
    CLI_ARG = "cliArg"


@dataclass
class PermissionRuleValue:
    tool_name: str = ""
    rule_content: str | None = None


@dataclass
class PermissionRule:
    source: PermissionRuleSource = PermissionRuleSource.SESSION
    rule_behavior: PermissionBehavior = PermissionBehavior.ASK
    rule_value: PermissionRuleValue = field(default_factory=PermissionRuleValue)


# ---------------------------------------------------------------------------
# Permission Updates
# ---------------------------------------------------------------------------


@dataclass
class AddRulesUpdate:
    type: Literal["addRules"] = "addRules"
    destination: PermissionUpdateDestination = PermissionUpdateDestination.SESSION
    rules: list[PermissionRuleValue] = field(default_factory=list)
    behavior: PermissionBehavior = PermissionBehavior.ALLOW


@dataclass
class ReplaceRulesUpdate:
    type: Literal["replaceRules"] = "replaceRules"
    destination: PermissionUpdateDestination = PermissionUpdateDestination.SESSION
    rules: list[PermissionRuleValue] = field(default_factory=list)
    behavior: PermissionBehavior = PermissionBehavior.ALLOW


@dataclass
class RemoveRulesUpdate:
    type: Literal["removeRules"] = "removeRules"
    destination: PermissionUpdateDestination = PermissionUpdateDestination.SESSION
    rules: list[PermissionRuleValue] = field(default_factory=list)
    behavior: PermissionBehavior = PermissionBehavior.ALLOW


@dataclass
class SetModeUpdate:
    type: Literal["setMode"] = "setMode"
    destination: PermissionUpdateDestination = PermissionUpdateDestination.SESSION
    mode: ExternalPermissionMode = "default"


@dataclass
class AddDirectoriesUpdate:
    type: Literal["addDirectories"] = "addDirectories"
    destination: PermissionUpdateDestination = PermissionUpdateDestination.SESSION
    directories: list[str] = field(default_factory=list)


@dataclass
class RemoveDirectoriesUpdate:
    type: Literal["removeDirectories"] = "removeDirectories"
    destination: PermissionUpdateDestination = PermissionUpdateDestination.SESSION
    directories: list[str] = field(default_factory=list)


PermissionUpdate = (
    AddRulesUpdate
    | ReplaceRulesUpdate
    | RemoveRulesUpdate
    | SetModeUpdate
    | AddDirectoriesUpdate
    | RemoveDirectoriesUpdate
)


# ---------------------------------------------------------------------------
# Working Directories
# ---------------------------------------------------------------------------

WorkingDirectorySource = PermissionRuleSource


@dataclass
class AdditionalWorkingDirectory:
    path: str = ""
    source: WorkingDirectorySource = PermissionRuleSource.SESSION


# ---------------------------------------------------------------------------
# Permission Decisions & Results
# ---------------------------------------------------------------------------


@dataclass
class PermissionCommandMetadata:
    name: str = ""
    description: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class PendingClassifierCheck:
    command: str = ""
    cwd: str = ""
    descriptions: list[str] = field(default_factory=list)


# Decision reason types


@dataclass
class RuleDecisionReason:
    type: Literal["rule"] = "rule"
    rule: PermissionRule = field(default_factory=PermissionRule)


@dataclass
class ModeDecisionReason:
    type: Literal["mode"] = "mode"
    mode: PermissionMode = PermissionMode.DEFAULT


@dataclass
class SubcommandDecisionReason:
    type: Literal["subcommandResults"] = "subcommandResults"
    reasons: dict[str, Any] = field(default_factory=dict)


@dataclass
class PermissionPromptToolDecisionReason:
    type: Literal["permissionPromptTool"] = "permissionPromptTool"
    permission_prompt_tool_name: str = ""
    tool_result: Any = None


@dataclass
class HookDecisionReason:
    type: Literal["hook"] = "hook"
    hook_name: str = ""
    hook_source: str | None = None
    reason: str | None = None


@dataclass
class AsyncAgentDecisionReason:
    type: Literal["asyncAgent"] = "asyncAgent"
    reason: str = ""


@dataclass
class SandboxOverrideDecisionReason:
    type: Literal["sandboxOverride"] = "sandboxOverride"
    reason: Literal["excludedCommand", "dangerouslyDisableSandbox"] = "excludedCommand"


@dataclass
class ClassifierDecisionReason:
    type: Literal["classifier"] = "classifier"
    classifier: str = ""
    reason: str = ""


@dataclass
class WorkingDirDecisionReason:
    type: Literal["workingDir"] = "workingDir"
    reason: str = ""


@dataclass
class SafetyCheckDecisionReason:
    type: Literal["safetyCheck"] = "safetyCheck"
    reason: str = ""
    classifier_approvable: bool = False


@dataclass
class OtherDecisionReason:
    type: Literal["other"] = "other"
    reason: str = ""


PermissionDecisionReason = (
    RuleDecisionReason
    | ModeDecisionReason
    | SubcommandDecisionReason
    | PermissionPromptToolDecisionReason
    | HookDecisionReason
    | AsyncAgentDecisionReason
    | SandboxOverrideDecisionReason
    | ClassifierDecisionReason
    | WorkingDirDecisionReason
    | SafetyCheckDecisionReason
    | OtherDecisionReason
)


# Permission decision types


@dataclass
class PermissionAllowDecision:
    behavior: Literal["allow"] = "allow"
    updated_input: dict[str, Any] | None = None
    user_modified: bool | None = None
    decision_reason: PermissionDecisionReason | None = None
    tool_use_id: str | None = None
    accept_feedback: str | None = None
    content_blocks: list[dict[str, Any]] | None = None


@dataclass
class PermissionAskDecision:
    behavior: Literal["ask"] = "ask"
    message: str = ""
    updated_input: dict[str, Any] | None = None
    decision_reason: PermissionDecisionReason | None = None
    suggestions: list[PermissionUpdate] | None = None
    blocked_path: str | None = None
    metadata: PermissionCommandMetadata | None = None
    is_bash_security_check_for_misparsing: bool | None = None
    pending_classifier_check: PendingClassifierCheck | None = None
    content_blocks: list[dict[str, Any]] | None = None


@dataclass
class PermissionDenyDecision:
    behavior: Literal["deny"] = "deny"
    message: str = ""
    decision_reason: PermissionDecisionReason | None = None
    tool_use_id: str | None = None


@dataclass
class PermissionPassthroughDecision:
    behavior: Literal["passthrough"] = "passthrough"
    message: str = ""
    decision_reason: PermissionDecisionReason | None = None
    suggestions: list[PermissionUpdate] | None = None
    blocked_path: str | None = None
    pending_classifier_check: PendingClassifierCheck | None = None


PermissionDecision = (
    PermissionAllowDecision | PermissionAskDecision | PermissionDenyDecision
)

PermissionResult = (
    PermissionAllowDecision
    | PermissionAskDecision
    | PermissionDenyDecision
    | PermissionPassthroughDecision
)


# ---------------------------------------------------------------------------
# Tool Permission Context
# ---------------------------------------------------------------------------

# Mapping from PermissionRuleSource -> list of rule strings
ToolPermissionRulesBySource = dict[PermissionRuleSource, list[str]]


@dataclass
class ToolPermissionContext:
    """Immutable permission context for tool execution."""

    mode: PermissionMode = PermissionMode.DEFAULT
    additional_working_directories: dict[str, AdditionalWorkingDirectory] = field(
        default_factory=dict
    )
    always_allow_rules: ToolPermissionRulesBySource = field(default_factory=dict)
    always_deny_rules: ToolPermissionRulesBySource = field(default_factory=dict)
    always_ask_rules: ToolPermissionRulesBySource = field(default_factory=dict)
    is_bypass_permissions_mode_available: bool = False
    is_auto_mode_available: bool | None = None
    stripped_dangerous_rules: ToolPermissionRulesBySource | None = None
    should_avoid_permission_prompts: bool | None = None
    await_automated_checks_before_dialog: bool | None = None
    pre_plan_mode: PermissionMode | None = None


def get_empty_tool_permission_context() -> ToolPermissionContext:
    """Return a default empty tool permission context."""
    return ToolPermissionContext()


# ---------------------------------------------------------------------------
# Classifier Types
# ---------------------------------------------------------------------------


class ClassifierConfidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ClassifierResult:
    matches: bool = False
    matched_description: str | None = None
    confidence: ClassifierConfidence = ClassifierConfidence.LOW
    reason: str = ""


@dataclass
class ClassifierUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


@dataclass
class YoloClassifierResult:
    thinking: str | None = None
    should_block: bool = False
    reason: str = ""
    unavailable: bool | None = None
    transcript_too_long: bool | None = None
    model: str = ""
    usage: ClassifierUsage | None = None
    duration_ms: float | None = None
    prompt_lengths: dict[str, int] | None = None
    error_dump_path: str | None = None
    stage: Literal["fast", "thinking"] | None = None
    stage1_usage: ClassifierUsage | None = None
    stage1_duration_ms: float | None = None
    stage2_usage: ClassifierUsage | None = None
    stage2_duration_ms: float | None = None


# ---------------------------------------------------------------------------
# Risk Level
# ---------------------------------------------------------------------------


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class PermissionExplanation:
    risk_level: RiskLevel = RiskLevel.LOW
    explanation: str = ""
    reasoning: str = ""
    risk: str = ""
