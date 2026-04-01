"""Application state definition.

Ports the TypeScript AppState from src/state/AppStateStore.ts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from code_assist.types.command import CommandBase
from code_assist.types.ids import AgentId
from code_assist.types.message import Message
from code_assist.types.permissions import (
    PermissionMode,
    ToolPermissionContext,
    get_empty_tool_permission_context,
)
from code_assist.types.plugin import LoadedPlugin
from code_assist.types.tools import SpinnerMode


# ---------------------------------------------------------------------------
# Supporting Types
# ---------------------------------------------------------------------------


@dataclass
class TaskState:
    """State of a background task."""

    task_id: str = ""
    task_type: str = ""  # local_bash, local_agent, remote_agent, etc.
    status: Literal["pending", "running", "completed", "failed", "killed"] = "pending"
    subject: str = ""
    description: str = ""
    active_form: str | None = None
    owner: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    blocks: list[str] = field(default_factory=list)
    blocked_by: list[str] = field(default_factory=list)
    output_file: str | None = None
    created_at: float = 0.0
    updated_at: float = 0.0


@dataclass
class MCPState:
    """State of MCP server connections."""

    clients: list[Any] = field(default_factory=list)  # MCPServerConnection
    tools: list[Any] = field(default_factory=list)  # Tool
    commands: list[CommandBase] = field(default_factory=list)
    resources: dict[str, list[Any]] = field(default_factory=dict)  # ServerResource
    plugin_reconnect_key: int = 0


@dataclass
class PluginState:
    """State of loaded plugins."""

    enabled: list[LoadedPlugin] = field(default_factory=list)
    disabled: list[LoadedPlugin] = field(default_factory=list)
    commands: list[CommandBase] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    needs_refresh: bool = False


@dataclass
class NotificationState:
    """Notification queue state."""

    current: dict[str, Any] | None = None
    queue: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ElicitationState:
    """Elicitation queue state."""

    queue: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class InboxState:
    """Agent message inbox."""

    messages: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PromptSuggestionState:
    """Prompt suggestion state."""

    text: str | None = None
    prompt_id: str | None = None
    shown_at: float = 0.0
    accepted_at: float = 0.0
    generation_request_id: str | None = None


@dataclass
class SessionHooksState:
    """Session hooks execution state."""

    has_run: bool = False
    is_running: bool = False
    error: str | None = None


@dataclass
class FileHistoryState:
    """File modification history tracking."""

    entries: dict[str, list[dict[str, Any]]] = field(default_factory=dict)


@dataclass
class AttributionState:
    """Commit attribution tracking."""

    commits: list[dict[str, Any]] = field(default_factory=list)
    prs: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DenialTrackingState:
    """Permission denial tracking for escalation."""

    consecutive_denials: int = 0
    last_denial_tool: str | None = None
    last_denial_time: float | None = None


@dataclass
class AgentDefinitionsResult:
    """Loaded agent definitions."""

    agents: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Footer Items
# ---------------------------------------------------------------------------


@dataclass
class FooterItem:
    type: Literal["tasks", "tmux", "teams", "bridge", "companion"] = "tasks"


# ---------------------------------------------------------------------------
# AppState
# ---------------------------------------------------------------------------


@dataclass
class AppState:
    """Complete application state.

    Matches the TypeScript AppState from AppStateStore.ts.
    Fields are organized into immutable (config-like) and mutable (runtime) groups.
    """

    # --- Settings & Config ---
    settings: dict[str, Any] = field(default_factory=dict)  # SettingsJson
    verbose: bool = False
    main_loop_model: str = ""
    main_loop_model_for_session: str = ""
    status_line_text: str | None = None
    agent: str | None = None

    # --- UI State ---
    expanded_view: Literal["none", "tasks", "teammates"] = "none"
    is_brief_only: bool = False
    show_teammate_message_preview: bool = False
    selected_ip_agent_index: int = 0
    coordinator_task_index: int = 0
    view_selection_mode: Literal["none", "selecting-agent", "viewing-agent"] = "none"
    footer_selection: FooterItem | None = None
    spinner_tip: str | None = None

    # --- Permissions ---
    tool_permission_context: ToolPermissionContext = field(
        default_factory=get_empty_tool_permission_context
    )

    # --- Feature Flags ---
    kairos_enabled: bool = False
    thinking_enabled: bool | None = None
    prompt_suggestion_enabled: bool = False
    fast_mode: bool | None = None
    advisor_model: str | None = None
    effort_value: str | None = None

    # --- Remote/Bridge ---
    remote_session_url: str | None = None
    remote_connection_status: Literal[
        "connecting", "connected", "reconnecting", "disconnected"
    ] = "disconnected"
    remote_background_task_count: int = 0
    repl_bridge_enabled: bool = False
    repl_bridge_explicit: bool = False
    repl_bridge_outbound_only: bool = False
    repl_bridge_connected: bool = False
    repl_bridge_session_active: bool = False
    repl_bridge_reconnecting: bool = False
    repl_bridge_connect_url: str | None = None
    repl_bridge_session_url: str | None = None
    repl_bridge_environment_id: str | None = None
    repl_bridge_session_id: str | None = None
    repl_bridge_error: str | None = None
    repl_bridge_initial_name: str | None = None
    show_remote_callout: bool = False

    # --- Tasks ---
    tasks: dict[str, TaskState] = field(default_factory=dict)
    foregrounded_task_id: str | None = None
    viewing_agent_task_id: str | None = None

    # --- Agent Registry ---
    agent_name_registry: dict[str, AgentId] = field(default_factory=dict)

    # --- MCP ---
    mcp: MCPState = field(default_factory=MCPState)

    # --- Plugins ---
    plugins: PluginState = field(default_factory=PluginState)

    # --- Agent Definitions ---
    agent_definitions: AgentDefinitionsResult = field(
        default_factory=AgentDefinitionsResult
    )

    # --- File History & Attribution ---
    file_history: FileHistoryState = field(default_factory=FileHistoryState)
    attribution: AttributionState = field(default_factory=AttributionState)

    # --- Todos ---
    todos: dict[str, dict[str, Any]] = field(default_factory=dict)

    # --- Notifications ---
    notifications: NotificationState = field(default_factory=NotificationState)
    elicitation: ElicitationState = field(default_factory=ElicitationState)

    # --- Session Hooks ---
    session_hooks: SessionHooksState = field(default_factory=SessionHooksState)

    # --- Inbox ---
    inbox: InboxState = field(default_factory=InboxState)

    # --- Prompt Suggestion ---
    prompt_suggestion: PromptSuggestionState = field(
        default_factory=PromptSuggestionState
    )

    # --- Denial Tracking ---
    denial_tracking: DenialTrackingState | None = None

    # --- Speculation ---
    speculation: dict[str, Any] = field(default_factory=dict)
    speculation_session_time_saved_ms: float = 0.0

    # --- Plan Mode ---
    pending_plan_verification: dict[str, Any] | None = None

    # --- Auth ---
    auth_version: int = 0
    initial_message: dict[str, Any] | None = None

    # --- Active Overlays ---
    active_overlays: set[str] = field(default_factory=set)

    # --- Team Context ---
    team_context: dict[str, Any] | None = None
    standalone_agent_context: dict[str, Any] | None = None

    # --- Companion ---
    companion_reaction: str | None = None
    companion_pet_at: float | None = None


def get_default_app_state() -> AppState:
    """Return a new default AppState instance."""
    return AppState()
