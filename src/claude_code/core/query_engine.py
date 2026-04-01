"""QueryEngine - higher-level orchestration for query execution.

Handles system prompt assembly, tool filtering, session management,
and exposes submit_message() as the primary API.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any

from claude_code.config.claude_md import build_claude_md_context, get_memory_files
from claude_code.config.managed_env import get_api_key
from claude_code.core.process_input import ProcessedInput, process_user_input
from claude_code.core.query import (
    DoneEvent,
    QueryConfig,
    QueryEvent,
    query,
)
from claude_code.services.api.claude import SystemPrompt, SystemPromptBlock
from claude_code.tools.base import ToolDef, ToolUseContext, Tools
from claude_code.tools.registry import filter_enabled_tools
from claude_code.types.message import Message, create_user_message
from claude_code.utils.model.model import resolve_model

logger = logging.getLogger(__name__)


@dataclass
class QueryEngineConfig:
    """Configuration for the QueryEngine."""

    cwd: str = ""
    project_root: str = ""
    tools: Tools = field(default_factory=list)
    commands: list[Any] = field(default_factory=list)
    mcp_clients: list[Any] = field(default_factory=list)
    agent_definitions: Any = None
    model: str = "claude-sonnet-4-6"
    max_turns: int = 100
    max_tokens: int = 16384
    api_key: str | None = None
    base_url: str | None = None
    custom_system_prompt: str | None = None
    append_system_prompt: str | None = None
    json_schema: dict[str, Any] | None = None


class QueryEngine:
    """Main query engine that orchestrates the agent loop.

    Provides submit_message() which:
    1. Builds the system prompt (instructions + CLAUDE.md + context)
    2. Filters available tools
    3. Delegates to the core query loop
    4. Yields events to the caller
    """

    def __init__(self, config: QueryEngineConfig) -> None:
        self._config = config
        self._messages: list[Message] = []
        self._total_turns = 0

    @property
    def messages(self) -> list[Message]:
        """Get the conversation message history."""
        return self._messages

    def _build_system_prompt(self) -> SystemPrompt:
        """Build the complete system prompt from all sources."""
        blocks: list[SystemPromptBlock] = []

        # Custom system prompt overrides everything
        if self._config.custom_system_prompt:
            blocks.append(
                SystemPromptBlock(text=self._config.custom_system_prompt)
            )
            return blocks

        # Core instructions
        blocks.append(
            SystemPromptBlock(
                text="You are an AI coding assistant. Help users with software engineering tasks.",
                cache_control={"type": "ephemeral"},
            )
        )

        # CLAUDE.md context
        memory_files = get_memory_files(
            self._config.project_root or self._config.cwd
        )
        claude_md_context = build_claude_md_context(memory_files)
        if claude_md_context:
            blocks.append(
                SystemPromptBlock(
                    text=f"# claudeMd\n{claude_md_context}",
                    cache_control={"type": "ephemeral"},
                )
            )

        # Appended system prompt
        if self._config.append_system_prompt:
            blocks.append(
                SystemPromptBlock(text=self._config.append_system_prompt)
            )

        return blocks

    def _build_context(self) -> ToolUseContext:
        """Build the tool use context."""
        return ToolUseContext(
            commands=self._config.commands,
            main_loop_model=self._config.model,
            tools=filter_enabled_tools(self._config.tools),
            mcp_clients=self._config.mcp_clients,
            agent_definitions=self._config.agent_definitions,
            messages=self._messages,
        )

    async def submit_message(
        self, prompt: str
    ) -> AsyncGenerator[QueryEvent, None]:
        """Submit a user message and stream the response.

        This is the primary API for the QueryEngine.
        """
        # Process input
        processed = process_user_input(prompt)

        if processed.is_command:
            # Command handling will be wired in Branch 19 (CLI entry)
            from claude_code.core.query import TextEvent
            yield TextEvent(text=f"Command /{processed.command_name} not yet wired.")
            return

        # Add user message
        user_msg = create_user_message(prompt)
        self._messages.append(user_msg)

        # Build config
        system_prompt = self._build_system_prompt()
        context = self._build_context()

        query_config = QueryConfig(
            model=resolve_model(self._config.model),
            max_tokens=self._config.max_tokens,
            max_turns=self._config.max_turns,
            system_prompt=system_prompt,
            tools=filter_enabled_tools(self._config.tools),
            api_key=self._config.api_key or get_api_key(),
            base_url=self._config.base_url,
        )

        # Execute query
        async for event in query(self._messages, query_config, context):
            if isinstance(event, DoneEvent):
                self._total_turns += event.total_turns
            yield event

    def clear_messages(self) -> None:
        """Clear the conversation history."""
        self._messages.clear()

    @property
    def total_turns(self) -> int:
        """Get total turns across all queries."""
        return self._total_turns
