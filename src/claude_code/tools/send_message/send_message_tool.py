"""SendMessage tool - sends a message to another agent by name or broadcasts.

Supports:
  - Direct message to a named teammate
  - Broadcast to all teammates via to="*"
  - Structured messages: shutdown_request, shutdown_response, plan_approval_response
"""

from __future__ import annotations

import logging
from typing import Any, Union

from pydantic import BaseModel, Field

from claude_code.tools.base import (
    CanUseToolFn,
    DescriptionOptions,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
    ValidationResult,
)
from claude_code.types.message import AssistantMessage

logger = logging.getLogger(__name__)


class SendMessageInput(BaseModel):
    """Input schema for SendMessage."""

    to: str = Field(
        ...,
        description='Recipient: teammate name, or "*" for broadcast to all teammates',
    )
    summary: str | None = Field(
        default=None,
        description="5-10 word summary shown as preview in the UI",
    )
    message: str | dict[str, Any] = Field(
        ...,
        description="Plain text message or structured message object",
    )


class SendMessageTool(ToolDef):
    """Send a message to another agent or broadcast to all teammates.

    Messages are routed through the team context in AppState. Each teammate
    has a mailbox where messages are queued for delivery.
    """

    name = "SendMessage"
    search_hint = "send message to teammate or broadcast"
    max_result_size_chars = 10_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return SendMessageInput

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        inp: SendMessageInput = input  # type: ignore[assignment]
        if not inp.to.strip():
            return ValidationResult(
                result=False, message="'to' field is required", error_code=1
            )
        if isinstance(inp.message, str) and not inp.message.strip():
            return ValidationResult(
                result=False, message="message content is required", error_code=2
            )
        return ValidationResult(result=True)

    def _get_team_context(self, context: ToolUseContext) -> dict[str, Any] | None:
        """Get the team context from AppState."""
        state = context.get_app_state()
        if isinstance(state, dict):
            return state.get("teamContext")
        if state is not None and hasattr(state, "teamContext"):
            return getattr(state, "teamContext", None)
        return None

    def _get_sender_name(self, context: ToolUseContext) -> str:
        """Get the name of the sending agent."""
        if context.agent_id:
            return context.agent_id
        return "main"

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        inp: SendMessageInput = args  # type: ignore[assignment]

        sender = self._get_sender_name(context)
        team_ctx = self._get_team_context(context)

        # Handle broadcast
        if inp.to == "*":
            return await self._broadcast(inp, sender, team_ctx, context)

        # Handle direct message
        return await self._send_direct(inp, sender, team_ctx, context)

    async def _broadcast(
        self,
        inp: SendMessageInput,
        sender: str,
        team_ctx: dict[str, Any] | None,
        context: ToolUseContext,
    ) -> ToolResult:
        """Broadcast a message to all teammates."""
        recipients: list[str] = []

        if team_ctx:
            teammates = team_ctx.get("teammates", {})
            for tid, info in teammates.items():
                name = info.get("name", tid) if isinstance(info, dict) else str(tid)
                if name != sender:
                    recipients.append(name)

        if not recipients:
            return ToolResult(
                data={
                    "success": False,
                    "message": "No teammates to broadcast to.",
                    "recipients": [],
                }
            )

        # Queue message for each recipient
        message_content = inp.message if isinstance(inp.message, str) else str(inp.message)

        def _queue_broadcast(state: Any) -> Any:
            if not isinstance(state, dict):
                return state
            mailboxes = dict(state.get("mailboxes", {}))
            for recipient in recipients:
                box = list(mailboxes.get(recipient, []))
                box.append({
                    "from": sender,
                    "to": recipient,
                    "content": message_content,
                    "summary": inp.summary,
                    "type": "broadcast",
                })
                mailboxes[recipient] = box
            return {**state, "mailboxes": mailboxes}

        context.set_app_state(_queue_broadcast)

        return ToolResult(
            data={
                "success": True,
                "message": f"Broadcast sent to {len(recipients)} teammate(s).",
                "recipients": recipients,
                "routing": {
                    "sender": sender,
                    "target": "*",
                    "summary": inp.summary,
                },
            }
        )

    async def _send_direct(
        self,
        inp: SendMessageInput,
        sender: str,
        team_ctx: dict[str, Any] | None,
        context: ToolUseContext,
    ) -> ToolResult:
        """Send a direct message to a named recipient."""
        recipient = inp.to.strip()
        message_content = inp.message if isinstance(inp.message, str) else str(inp.message)

        # Queue message in mailbox
        def _queue_message(state: Any) -> Any:
            if not isinstance(state, dict):
                return state
            mailboxes = dict(state.get("mailboxes", {}))
            box = list(mailboxes.get(recipient, []))
            box.append({
                "from": sender,
                "to": recipient,
                "content": message_content,
                "summary": inp.summary,
            })
            mailboxes[recipient] = box
            return {**state, "mailboxes": mailboxes}

        context.set_app_state(_queue_message)

        # Determine recipient color for routing info
        recipient_color = None
        if team_ctx:
            teammates = team_ctx.get("teammates", {})
            for info in teammates.values():
                if isinstance(info, dict) and info.get("name") == recipient:
                    recipient_color = info.get("color")
                    break

        return ToolResult(
            data={
                "success": True,
                "message": f"Message sent to {recipient}.",
                "routing": {
                    "sender": sender,
                    "target": recipient,
                    "targetColor": recipient_color,
                    "summary": inp.summary,
                    "content": message_content[:100],
                },
            }
        )

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        inp: SendMessageInput = input  # type: ignore[assignment]
        return f"Sending message to {inp.to}"

    def is_read_only(self, input: BaseModel) -> bool:
        return False

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True
