"""API key and authentication management."""

import logging
import os
from dataclasses import dataclass
from enum import StrEnum

logger = logging.getLogger(__name__)


class AuthSource(StrEnum):
    USER = "user"
    PROJECT = "project"
    ORG = "org"
    TEMPORARY = "temporary"
    OAUTH = "oauth"


@dataclass
class AuthState:
    api_key: str | None = None
    source: AuthSource = AuthSource.USER
    is_authenticated: bool = False
    user_id: str | None = None
    org_id: str | None = None


def get_api_key() -> str | None:
    """Get API key from environment or config."""
    return os.environ.get("ANTHROPIC_API_KEY")


def get_auth_state() -> AuthState:
    """Determine current authentication state."""
    key = get_api_key()
    if key:
        source = AuthSource.USER
        if key.startswith("sk-ant-"):
            source = AuthSource.USER
        return AuthState(api_key=key, source=source, is_authenticated=True)
    return AuthState()


def validate_api_key(key: str) -> bool:
    """Basic validation that a key looks like an API key."""
    return bool(key) and (key.startswith("sk-ant-") or key.startswith("sk-"))


def mask_api_key(key: str) -> str:
    """Mask an API key for display."""
    if len(key) <= 8:
        return "***"
    return key[:7] + "..." + key[-4:]
