"""Grep tool - content search powered by ripgrep.

Shells out to rg (ripgrep) for fast content search with regex support.
Falls back to a pure-Python implementation when rg is unavailable.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from code_assist.tools.base import (
    CanUseToolFn,
    SearchOrReadInfo,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
)
from code_assist.types.message import AssistantMessage


# ---------------------------------------------------------------------------
# Input Schema
# ---------------------------------------------------------------------------


class GrepInput(BaseModel):
    """Input for the Grep tool."""

    pattern: str = Field(description="Regex pattern to search for")
    path: str | None = Field(
        default=None,
        description="File or directory to search in. Defaults to cwd.",
    )
    glob: str | None = Field(
        default=None,
        description="Glob pattern to filter files (e.g. '*.py').",
    )
    type: str | None = Field(
        default=None,
        description="File type filter for ripgrep (e.g. 'py', 'js').",
    )
    output_mode: Literal["content", "files_with_matches", "count"] = Field(
        default="files_with_matches",
        description="Output mode: content, files_with_matches, or count.",
    )
    context: int | None = Field(
        default=None,
        description="Lines of context around matches (-C).",
    )
    # Pydantic field names cannot start with '-', so we use aliases
    after_context: int | None = Field(
        default=None,
        alias="-A",
        description="Lines after each match (-A).",
    )
    before_context: int | None = Field(
        default=None,
        alias="-B",
        description="Lines before each match (-B).",
    )
    case_insensitive: bool = Field(
        default=False,
        alias="-i",
        description="Case insensitive search.",
    )
    line_numbers: bool = Field(
        default=True,
        alias="-n",
        description="Show line numbers.",
    )
    multiline: bool = Field(
        default=False,
        description="Enable multiline matching.",
    )
    head_limit: int = Field(
        default=250,
        description="Max lines/entries to return.",
    )
    offset: int = Field(
        default=0,
        description="Skip first N entries before applying head_limit.",
    )

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Tool Implementation
# ---------------------------------------------------------------------------


class GrepTool(ToolDef):
    """Content search tool powered by ripgrep.

    Uses rg for fast regex search across files. Falls back to Python re
    module when ripgrep is not installed.
    """

    name = "Grep"
    search_hint = "search content regex pattern grep ripgrep"
    max_result_size_chars = 100_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return GrepInput

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        input_args: GrepInput = args  # type: ignore[assignment]

        rg_path = shutil.which("rg")
        if rg_path:
            return await self._run_ripgrep(input_args)
        return await self._run_python_fallback(input_args)

    # -----------------------------------------------------------------
    # ripgrep backend
    # -----------------------------------------------------------------

    async def _run_ripgrep(self, args: GrepInput) -> ToolResult:
        cmd = ["rg"]

        # Output mode
        if args.output_mode == "files_with_matches":
            cmd.append("--files-with-matches")
        elif args.output_mode == "count":
            cmd.append("--count")
        # "content" is default rg behaviour

        # Context flags (only useful in content mode)
        if args.output_mode == "content":
            if args.context is not None:
                cmd.extend(["-C", str(args.context)])
            if args.after_context is not None:
                cmd.extend(["-A", str(args.after_context)])
            if args.before_context is not None:
                cmd.extend(["-B", str(args.before_context)])
            if args.line_numbers:
                cmd.append("-n")

        # Flags
        if args.case_insensitive:
            cmd.append("-i")
        if args.multiline:
            cmd.extend(["-U", "--multiline-dotall"])

        # File filters
        if args.glob:
            cmd.extend(["--glob", args.glob])
        if args.type:
            cmd.extend(["--type", args.type])

        # Pattern
        cmd.extend(["--", args.pattern])

        # Search path
        search_path = args.path or "."
        cmd.append(search_path)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(data="Error: search timed out after 30 seconds")
        except FileNotFoundError:
            return ToolResult(data="Error: rg (ripgrep) not found")

        output = result.stdout
        if result.returncode == 1:
            # No matches
            return ToolResult(data="No matches found.")
        if result.returncode not in (0, 1):
            return ToolResult(data=f"Error: {result.stderr.strip()}")

        # Apply offset and head_limit
        lines = output.splitlines()
        if args.offset > 0:
            lines = lines[args.offset:]
        if args.head_limit > 0:
            lines = lines[: args.head_limit]

        return ToolResult(data="\n".join(lines) if lines else "No matches found.")

    # -----------------------------------------------------------------
    # Python fallback
    # -----------------------------------------------------------------

    async def _run_python_fallback(self, args: GrepInput) -> ToolResult:
        search_path = Path(args.path) if args.path else Path.cwd()

        flags = 0
        if args.case_insensitive:
            flags |= re.IGNORECASE
        if args.multiline:
            flags |= re.MULTILINE | re.DOTALL

        try:
            regex = re.compile(args.pattern, flags)
        except re.error as exc:
            return ToolResult(data=f"Error: invalid regex: {exc}")

        results: list[str] = []

        if search_path.is_file():
            files = [search_path]
        elif search_path.is_dir():
            glob_pattern = args.glob or "**/*"
            files = [f for f in search_path.glob(glob_pattern) if f.is_file()]
            if args.type:
                ext = f".{args.type}"
                files = [f for f in files if f.suffix == ext]
        else:
            return ToolResult(data=f"Error: path '{search_path}' not found")

        for file_path in sorted(files):
            try:
                content = file_path.read_text(errors="replace")
            except (OSError, PermissionError):
                continue

            if args.output_mode == "files_with_matches":
                if regex.search(content):
                    results.append(str(file_path))
            elif args.output_mode == "count":
                count = len(regex.findall(content))
                if count > 0:
                    results.append(f"{file_path}:{count}")
            else:  # content
                for i, line in enumerate(content.splitlines(), 1):
                    if regex.search(line):
                        prefix = f"{i}:" if args.line_numbers else ""
                        results.append(f"{file_path}:{prefix}{line}")

        # Apply offset and head_limit
        if args.offset > 0:
            results = results[args.offset:]
        if args.head_limit > 0:
            results = results[: args.head_limit]

        return ToolResult(data="\n".join(results) if results else "No matches found.")

    async def description(self, input: BaseModel, options: Any) -> str:
        args: GrepInput = input  # type: ignore[assignment]
        return f"Grep: {args.pattern}"

    def is_read_only(self, input: BaseModel) -> bool:
        return True

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True

    def is_search_or_read_command(self, input: BaseModel) -> SearchOrReadInfo:
        return SearchOrReadInfo(is_search=True)
