"""OAuth 2.0 PKCE client for claude.ai authentication."""

import base64
import hashlib
import logging
import secrets
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PKCEChallenge:
    code_verifier: str = ""
    code_challenge: str = ""
    code_challenge_method: str = "S256"


def generate_pkce_challenge() -> PKCEChallenge:
    """Generate a PKCE code verifier and challenge pair."""
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return PKCEChallenge(code_verifier=verifier, code_challenge=challenge)


@dataclass
class OAuthTokens:
    access_token: str = ""
    refresh_token: str = ""
    expires_at: float = 0.0
    token_type: str = "Bearer"

    @property
    def is_expired(self) -> bool:
        return time.time() >= self.expires_at
