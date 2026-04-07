"""Language Server Protocol server lifecycle management."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LSPServerConfig:
    """Configuration for an LSP server."""

    language: str = ""
    command: str = ""
    args: list[str] = field(default_factory=list)
    root_uri: str = ""
    initialization_options: dict[str, Any] = field(default_factory=dict)


@dataclass
class LSPServer:
    """An active LSP server connection."""

    config: LSPServerConfig = field(default_factory=LSPServerConfig)
    process: asyncio.subprocess.Process | None = None
    is_initialized: bool = False
    capabilities: dict[str, Any] = field(default_factory=dict)
    request_id: int = 0

    def next_request_id(self) -> int:
        self.request_id += 1
        return self.request_id


class LSPManager:
    """Manages LSP server lifecycles."""

    def __init__(self) -> None:
        self._servers: dict[str, LSPServer] = {}

    async def start_server(self, config: LSPServerConfig) -> LSPServer:
        """Start an LSP server process and initialize it."""
        server = LSPServer(config=config)

        try:
            server.process = await asyncio.create_subprocess_exec(
                config.command,
                *config.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Send initialize request
            init_params = {
                "processId": None,
                "rootUri": config.root_uri,
                "capabilities": {
                    "textDocument": {
                        "definition": {"dynamicRegistration": False},
                        "references": {"dynamicRegistration": False},
                        "hover": {"contentFormat": ["markdown", "plaintext"]},
                        "documentSymbol": {"dynamicRegistration": False},
                    },
                    "workspace": {
                        "symbol": {"dynamicRegistration": False},
                    },
                },
                "initializationOptions": config.initialization_options,
            }

            response = await self._send_request(server, "initialize", init_params)
            if response:
                server.capabilities = response.get("capabilities", {})
                await self._send_notification(server, "initialized", {})
                server.is_initialized = True

            self._servers[config.language] = server
            return server

        except (FileNotFoundError, OSError) as e:
            logger.warning("Failed to start LSP server for %s: %s", config.language, e)
            return server

    async def stop_server(self, language: str) -> None:
        """Stop an LSP server."""
        server = self._servers.pop(language, None)
        if server and server.process:
            try:
                await self._send_request(server, "shutdown", None)
                await self._send_notification(server, "exit", None)
                server.process.terminate()
                await asyncio.wait_for(server.process.wait(), timeout=5.0)
            except Exception:
                if server.process:
                    server.process.kill()

    async def stop_all(self) -> None:
        """Stop all LSP servers."""
        for language in list(self._servers.keys()):
            await self.stop_server(language)

    def get_server(self, language: str) -> LSPServer | None:
        """Get an LSP server by language."""
        return self._servers.get(language)

    async def send_request(
        self, language: str, method: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Send a request to an LSP server."""
        server = self._servers.get(language)
        if not server or not server.is_initialized:
            return None
        return await self._send_request(server, method, params)

    async def _send_request(
        self, server: LSPServer, method: str, params: Any
    ) -> dict[str, Any] | None:
        """Send a JSON-RPC request and wait for response."""
        if not server.process or not server.process.stdin or not server.process.stdout:
            return None

        request_id = server.next_request_id()
        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        content = json.dumps(message)
        header = f"Content-Length: {len(content)}\r\n\r\n"
        server.process.stdin.write((header + content).encode())
        await server.process.stdin.drain()

        # Read response
        try:
            response_data = await asyncio.wait_for(
                self._read_response(server), timeout=30.0
            )
            if response_data and response_data.get("id") == request_id:
                return response_data.get("result")
        except asyncio.TimeoutError:
            logger.warning("LSP request timed out: %s", method)

        return None

    async def _send_notification(
        self, server: LSPServer, method: str, params: Any
    ) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        if not server.process or not server.process.stdin:
            return

        message = {"jsonrpc": "2.0", "method": method, "params": params}
        content = json.dumps(message)
        header = f"Content-Length: {len(content)}\r\n\r\n"
        server.process.stdin.write((header + content).encode())
        await server.process.stdin.drain()

    async def _read_response(self, server: LSPServer) -> dict[str, Any] | None:
        """Read a JSON-RPC response from the LSP server."""
        if not server.process or not server.process.stdout:
            return None

        # Read Content-Length header
        header_line = await server.process.stdout.readline()
        if not header_line:
            return None

        header_text = header_line.decode(errors="replace").strip()
        if not header_text.startswith("Content-Length:"):
            return None

        content_length = int(header_text.split(":")[1].strip())
        await server.process.stdout.readline()  # Empty line
        content = await server.process.stdout.readexactly(content_length)
        return json.loads(content.decode())
