"""Bash tool implementation.

Executes shell commands via asyncio subprocess, with timeout support,
background execution, and safety analysis.
"""

from __future__ import annotations

import asyncio
from typing import Any

from pydantic import BaseModel, Field

from claude_code.tools.base import (
    CanUseToolFn,
    DescriptionOptions,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
)
from claude_code.tools.bash.command_semantics import classify_command
from claude_code.tools.bash.read_only_validation import validate_read_only
from claude_code.types.message import AssistantMessage
from claude_code.types.tools import BashProgress, ToolProgress

# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------

MAX_TIMEOUT_MS = 600_000  # 10 minutes


class BashInput(BaseModel):
    """Input schema for the Bash tool."""

    command: str = Field(..., description="The shell command to execute")
    description: str | None = Field(
        default=None,
        description="Human-readable description of what the command does",
    )
    timeout: int | None = Field(
        default=None,
        description="Timeout in milliseconds (max 600000)",
        le=MAX_TIMEOUT_MS,
    )
    run_in_background: bool = Field(
        default=False,
        description="Run the command in the background",
    )


# ---------------------------------------------------------------------------
# BashTool
# ---------------------------------------------------------------------------


class BashTool(ToolDef):
    """Execute shell commands with safety analysis and timeout support."""

    name = "Bash"
    max_result_size_chars = 100_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return BashInput

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        """Execute a shell command and return its output."""
        inp: BashInput = args  # type: ignore[assignment]

        timeout_s = (
            min(inp.timeout, MAX_TIMEOUT_MS) / 1000
            if inp.timeout is not None
            else MAX_TIMEOUT_MS / 1000
        )

        try:
            proc = await asyncio.create_subprocess_shell(
                inp.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as exc:
            return ToolResult(data=f"Failed to start command: {exc}")

        pid = proc.pid

        # Report initial progress
        if on_progress and context.tool_use_id:
            on_progress(
                ToolProgress(
                    tool_use_id=context.tool_use_id,
                    data=BashProgress(
                        command=inp.command,
                        pid=pid,
                        is_background=inp.run_in_background,
                    ),
                )
            )

        # Background mode: return immediately
        if inp.run_in_background:
            return ToolResult(
                data=f"Command started in background (pid={pid}): {inp.command}"
            )

        # Foreground mode: wait with timeout
        timed_out = False
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout_s
            )
        except asyncio.TimeoutError:
            timed_out = True
            proc.kill()
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(), timeout=5.0
                )
            except asyncio.TimeoutError:
                stdout_bytes, stderr_bytes = b"", b""

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        exit_code = proc.returncode

        # Build output
        output_parts: list[str] = []
        if stdout:
            output_parts.append(stdout)
        if stderr:
            output_parts.append(f"STDERR:\n{stderr}")
        if timed_out:
            output_parts.append(f"\n[Command timed out after {timeout_s}s]")
        if exit_code and exit_code != 0:
            output_parts.append(f"\n[Exit code: {exit_code}]")

        output = "\n".join(output_parts) if output_parts else "(no output)"

        # Truncate if needed
        if len(output) > self.max_result_size_chars:
            output = output[: self.max_result_size_chars] + "\n... [truncated]"

        # Report completion
        if on_progress and context.tool_use_id:
            on_progress(
                ToolProgress(
                    tool_use_id=context.tool_use_id,
                    data=BashProgress(
                        command=inp.command,
                        output=output,
                        is_complete=True,
                        exit_code=exit_code,
                        pid=pid,
                        timed_out=timed_out,
                    ),
                )
            )

        return ToolResult(data=output)

    async def description(
        self,
        input: BaseModel,
        options: DescriptionOptions,
    ) -> str:
        inp: BashInput = input  # type: ignore[assignment]
        if inp.description:
            return inp.description
        cmd = inp.command
        if len(cmd) > 80:
            cmd = cmd[:77] + "..."
        return cmd

    def is_read_only(self, input: BaseModel) -> bool:
        """Check if the command is read-only using command analysis."""
        inp: BashInput = input  # type: ignore[assignment]
        return validate_read_only(inp.command)

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        """Read-only commands are safe for concurrent execution."""
        return self.is_read_only(input)

    def is_destructive(self, input: BaseModel) -> bool:
        """Check if the command performs irreversible operations."""
        inp: BashInput = input  # type: ignore[assignment]
        semantics = classify_command(inp.command)
        return semantics.is_write and not semantics.is_read
