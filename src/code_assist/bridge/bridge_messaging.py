"""Bridge message exchange utilities."""

from __future__ import annotations

from typing import Any

from code_assist.bridge.bridge_api import BridgeConnection


async def send_selection_to_bridge(
    connection: BridgeConnection,
    file_path: str,
    start_line: int,
    end_line: int,
) -> None:
    """Send a file selection to the IDE."""
    await connection.send_message("select_range", {
        "path": file_path,
        "startLine": start_line,
        "endLine": end_line,
    })


async def open_file_in_ide(
    connection: BridgeConnection,
    file_path: str,
    line: int | None = None,
) -> None:
    """Open a file in the IDE, optionally at a specific line."""
    payload: dict[str, Any] = {"path": file_path}
    if line is not None:
        payload["line"] = line
    await connection.send_message("open_file", payload)


async def show_diff_in_ide(
    connection: BridgeConnection,
    file_path: str,
    original_content: str,
    modified_content: str,
) -> None:
    """Show a diff view in the IDE."""
    await connection.send_message("show_diff", {
        "path": file_path,
        "original": original_content,
        "modified": modified_content,
    })
