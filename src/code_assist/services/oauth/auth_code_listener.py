"""Local HTTP server for OAuth callback."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AuthCodeResult:
    code: str = ""
    state: str = ""
    error: str | None = None


async def start_auth_listener(
    port: int = 19485, timeout: float = 120.0
) -> AuthCodeResult:
    """Start a local HTTP server to receive OAuth callback. Placeholder."""
    logger.info("OAuth listener would start on port %d", port)
    return AuthCodeResult(error="OAuth not yet implemented")
