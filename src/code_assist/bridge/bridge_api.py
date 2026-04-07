"""IDE bridge protocol for VS Code / JetBrains integration."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BridgeConfig:
    """Bridge connection configuration."""

    host: str = "localhost"
    port: int = 0
    token: str = ""
    ide_type: str = ""  # vscode, jetbrains
    workspace_path: str = ""


@dataclass
class BridgeMessage:
    """Message in the bridge protocol."""

    type: str = ""
    id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


class BridgeConnection:
    """Manages connection to an IDE bridge."""

    def __init__(self, config: BridgeConfig) -> None:
        self._config = config
        self._connected = False
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self._message_id = 0

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> bool:
        """Establish connection to the IDE bridge."""
        if not self._config.port:
            return False

        try:
            self._reader, self._writer = await asyncio.open_connection(
                self._config.host, self._config.port
            )
            self._connected = True
            logger.info(
                "Connected to %s bridge at %s:%d",
                self._config.ide_type,
                self._config.host,
                self._config.port,
            )
            return True
        except (ConnectionRefusedError, OSError) as e:
            logger.warning("Failed to connect to IDE bridge: %s", e)
            return False

    async def disconnect(self) -> None:
        """Close the bridge connection."""
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
        self._connected = False

    async def send_message(self, msg_type: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Send a message and wait for response."""
        if not self._connected or not self._writer:
            return None

        self._message_id += 1
        msg_id = str(self._message_id)

        message = BridgeMessage(type=msg_type, id=msg_id, payload=payload)
        data = json.dumps({"type": message.type, "id": message.id, "payload": message.payload})

        try:
            self._writer.write((data + "\n").encode())
            await self._writer.drain()

            # Read response
            if self._reader:
                line = await asyncio.wait_for(self._reader.readline(), timeout=10.0)
                if line:
                    return json.loads(line.decode())
        except (asyncio.TimeoutError, OSError, json.JSONDecodeError) as e:
            logger.warning("Bridge communication error: %s", e)

        return None

    async def notify_file_changed(self, file_path: str, action: str = "modified") -> None:
        """Notify the IDE of a file change."""
        await self.send_message("file_changed", {"path": file_path, "action": action})

    async def get_diagnostics(self, file_path: str) -> list[dict[str, Any]]:
        """Get diagnostics from the IDE for a file."""
        response = await self.send_message("get_diagnostics", {"path": file_path})
        if response and "diagnostics" in response:
            return response["diagnostics"]
        return []

    async def execute_command(self, command: str, args: dict[str, Any] | None = None) -> Any:
        """Execute an IDE command."""
        response = await self.send_message("execute_command", {
            "command": command,
            "arguments": args or {},
        })
        return response.get("result") if response else None
