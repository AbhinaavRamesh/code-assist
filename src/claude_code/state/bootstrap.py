"""Session-level global state (singletons).

Session-level global state (singletons).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from claude_code.types.ids import SessionId, generate_session_id
from claude_code.types.message import ModelUsage


@dataclass
class BootstrapState:
    """Session-level global state that persists across the entire session.

    Session-level global state that persists across the entire session.
    Unlike AppState (which is store-managed), this holds singletons like counters,
    telemetry, and session metadata.
    """

    # --- Core Paths ---
    original_cwd: str = ""
    project_root: str = ""
    cwd: str = ""

    # --- Session Identity ---
    session_id: SessionId = field(default_factory=generate_session_id)
    parent_session_id: SessionId | None = None
    client_type: str = "cli"
    session_source: str | None = None

    # --- Cost & Duration Tracking ---
    total_cost_usd: float = 0.0
    total_api_duration: float = 0.0
    total_api_duration_without_retries: float = 0.0
    total_tool_duration: float = 0.0
    start_time: float = field(default_factory=time.time)
    last_interaction_time: float = field(default_factory=time.time)

    # --- Per-Turn Metrics ---
    turn_hook_duration_ms: float = 0.0
    turn_tool_duration_ms: float = 0.0
    turn_classifier_duration_ms: float = 0.0
    turn_tool_count: int = 0
    turn_hook_count: int = 0
    turn_classifier_count: int = 0

    # --- Code Change Tracking ---
    total_lines_added: int = 0
    total_lines_removed: int = 0

    # --- Model Usage ---
    model_usage: dict[str, ModelUsage] = field(default_factory=dict)
    main_loop_model_override: str | None = None
    initial_main_loop_model: str = ""
    has_unknown_model_cost: bool = False

    # --- Session Flags ---
    is_interactive: bool = True
    kairos_active: bool = False
    strict_tool_result_pairing: bool = False
    user_msg_opt_in: bool = False
    session_bypass_permissions_mode: bool = False
    session_trust_accepted: bool = False
    session_persistence_disabled: bool = False
    has_exited_plan_mode: bool = False
    needs_plan_mode_exit_attachment: bool = False
    needs_auto_mode_exit_attachment: bool = False
    is_remote_mode: bool = False

    # --- Settings Sources ---
    flag_settings_path: str | None = None
    flag_settings_inline: dict[str, Any] | None = None
    allowed_setting_sources: list[str] = field(default_factory=list)

    # --- Auth Tokens ---
    session_ingress_token: str | None = None
    oauth_token_from_fd: str | None = None
    api_key_from_fd: str | None = None

    # --- Agent Colors ---
    agent_color_map: dict[str, str] = field(default_factory=dict)
    agent_color_index: int = 0

    # --- API Request Cache ---
    last_api_request: dict[str, Any] | None = None
    last_api_request_messages: list[dict[str, Any]] | None = None
    last_classifier_requests: list[Any] | None = None

    # --- CLAUDE.md Cache ---
    cached_claude_md_content: str | None = None

    # --- Error Log ---
    in_memory_error_log: list[dict[str, str]] = field(default_factory=list)

    # --- Plugins ---
    inline_plugins: list[str] = field(default_factory=list)
    use_cowork_plugins: bool = False

    # --- Scheduled Tasks ---
    scheduled_tasks_enabled: bool = False
    session_cron_tasks: list[dict[str, Any]] = field(default_factory=list)
    session_created_teams: set[str] = field(default_factory=set)

    # --- Hooks ---
    registered_hooks: dict[str, list[Any]] | None = None

    # --- Plan Cache ---
    plan_slug_cache: dict[str, str] = field(default_factory=dict)

    # --- Skills ---
    invoked_skills: dict[str, dict[str, Any]] = field(default_factory=dict)

    # --- Performance ---
    slow_operations: list[dict[str, Any]] = field(default_factory=list)

    # --- SDK ---
    sdk_betas: list[str] | None = None
    main_thread_agent_type: str | None = None

    # --- System Prompt Cache ---
    system_prompt_section_cache: dict[str, str | None] = field(default_factory=dict)
    last_emitted_date: str | None = None
    additional_directories_for_claude_md: list[str] = field(default_factory=list)

    # --- Channels ---
    allowed_channels: list[dict[str, Any]] = field(default_factory=list)
    has_dev_channels: bool = False

    # --- Project ---
    session_project_dir: str | None = None

    # --- Cache Headers ---
    prompt_cache_1h_allowlist: list[str] | None = None
    prompt_cache_1h_eligible: bool | None = None
    afk_mode_header_latched: bool | None = None
    fast_mode_header_latched: bool | None = None

    # --- Request Tracking ---
    prompt_id: str | None = None
    last_main_request_id: str | None = None

    def reset_turn_metrics(self) -> None:
        """Reset per-turn counters at the start of each turn."""
        self.turn_hook_duration_ms = 0.0
        self.turn_tool_duration_ms = 0.0
        self.turn_classifier_duration_ms = 0.0
        self.turn_tool_count = 0
        self.turn_hook_count = 0
        self.turn_classifier_count = 0

    def add_cost(self, cost_usd: float) -> None:
        """Add to total session cost."""
        self.total_cost_usd += cost_usd

    def log_error(self, error: str) -> None:
        """Append an error to the in-memory error log."""
        import datetime

        self.in_memory_error_log.append(
            {"error": error, "timestamp": datetime.datetime.now(tz=datetime.UTC).isoformat()}
        )


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

_bootstrap_state: BootstrapState | None = None


def get_bootstrap_state() -> BootstrapState:
    """Get the global bootstrap state singleton."""
    global _bootstrap_state
    if _bootstrap_state is None:
        _bootstrap_state = BootstrapState()
    return _bootstrap_state


def reset_bootstrap_state() -> None:
    """Reset the global bootstrap state (for testing)."""
    global _bootstrap_state
    _bootstrap_state = None


def init_bootstrap_state(
    *,
    cwd: str = "",
    project_root: str = "",
    is_interactive: bool = True,
) -> BootstrapState:
    """Initialize the bootstrap state with starting values."""
    global _bootstrap_state
    _bootstrap_state = BootstrapState(
        original_cwd=cwd,
        cwd=cwd,
        project_root=project_root,
        is_interactive=is_interactive,
    )
    return _bootstrap_state
