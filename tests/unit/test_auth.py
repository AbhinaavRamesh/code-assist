"""Tests for auth system - API key management, OAuth PKCE, keychain storage."""

import base64
import hashlib
import time
from unittest.mock import MagicMock, patch

import pytest

from claude_code.services.oauth.auth_code_listener import (
    AuthCodeResult,
    start_auth_listener,
)
from claude_code.services.oauth.client import (
    OAuthTokens,
    PKCEChallenge,
    generate_pkce_challenge,
)
from claude_code.services.oauth.crypto import (
    generate_pkce_challenge as crypto_generate_pkce,
)
from claude_code.utils.auth import (
    AuthSource,
    AuthState,
    get_api_key,
    get_auth_state,
    mask_api_key,
    validate_api_key,
)
from claude_code.utils.secure_storage.keychain import (
    SERVICE_NAME,
    delete_credential,
    get_credential,
    store_credential,
)


# ---------------------------------------------------------------------------
# Auth state detection
# ---------------------------------------------------------------------------


class TestGetApiKey:
    def test_returns_key_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test123")
        assert get_api_key() == "sk-ant-test123"

    def test_returns_none_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        assert get_api_key() is None


class TestGetAuthState:
    def test_authenticated_with_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test123")
        state = get_auth_state()
        assert state.is_authenticated is True
        assert state.api_key == "sk-ant-test123"
        assert state.source == AuthSource.USER

    def test_unauthenticated_without_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        state = get_auth_state()
        assert state.is_authenticated is False
        assert state.api_key is None

    def test_auth_state_defaults(self) -> None:
        state = AuthState()
        assert state.api_key is None
        assert state.source == AuthSource.USER
        assert state.is_authenticated is False
        assert state.user_id is None
        assert state.org_id is None

    def test_auth_source_values(self) -> None:
        assert AuthSource.USER == "user"
        assert AuthSource.PROJECT == "project"
        assert AuthSource.ORG == "org"
        assert AuthSource.TEMPORARY == "temporary"
        assert AuthSource.OAUTH == "oauth"


# ---------------------------------------------------------------------------
# API key validation and masking
# ---------------------------------------------------------------------------


class TestValidateApiKey:
    def test_valid_sk_ant_key(self) -> None:
        assert validate_api_key("sk-ant-abc123") is True

    def test_valid_sk_key(self) -> None:
        assert validate_api_key("sk-test-key") is True

    def test_empty_string(self) -> None:
        assert validate_api_key("") is False

    def test_invalid_prefix(self) -> None:
        assert validate_api_key("invalid-key") is False


class TestMaskApiKey:
    def test_long_key(self) -> None:
        masked = mask_api_key("sk-ant-abc123456789xyz")
        assert masked == "sk-ant-...9xyz"
        assert "abc12345678" not in masked

    def test_short_key(self) -> None:
        assert mask_api_key("short") == "***"

    def test_boundary_length(self) -> None:
        # Exactly 8 characters should still be masked completely
        assert mask_api_key("12345678") == "***"

    def test_nine_chars(self) -> None:
        # 9 characters: show first 7 + ... + last 4
        result = mask_api_key("123456789")
        assert result == "1234567...6789"


# ---------------------------------------------------------------------------
# PKCE challenge generation
# ---------------------------------------------------------------------------


class TestPKCEChallenge:
    def test_generates_verifier_and_challenge(self) -> None:
        pkce = generate_pkce_challenge()
        assert pkce.code_verifier
        assert pkce.code_challenge
        assert pkce.code_challenge_method == "S256"

    def test_challenge_matches_verifier(self) -> None:
        pkce = generate_pkce_challenge()
        digest = hashlib.sha256(pkce.code_verifier.encode("ascii")).digest()
        expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        assert pkce.code_challenge == expected

    def test_unique_per_call(self) -> None:
        a = generate_pkce_challenge()
        b = generate_pkce_challenge()
        assert a.code_verifier != b.code_verifier
        assert a.code_challenge != b.code_challenge

    def test_crypto_wrapper_works(self) -> None:
        pkce = crypto_generate_pkce()
        assert isinstance(pkce, PKCEChallenge)
        assert pkce.code_verifier
        assert pkce.code_challenge


class TestOAuthTokens:
    def test_not_expired(self) -> None:
        tokens = OAuthTokens(
            access_token="tok",
            expires_at=time.time() + 3600,
        )
        assert tokens.is_expired is False

    def test_expired(self) -> None:
        tokens = OAuthTokens(
            access_token="tok",
            expires_at=time.time() - 10,
        )
        assert tokens.is_expired is True

    def test_defaults(self) -> None:
        tokens = OAuthTokens()
        assert tokens.access_token == ""
        assert tokens.refresh_token == ""
        assert tokens.token_type == "Bearer"


# ---------------------------------------------------------------------------
# OAuth auth code listener
# ---------------------------------------------------------------------------


class TestAuthCodeListener:
    async def test_placeholder_returns_error(self) -> None:
        result = await start_auth_listener()
        assert isinstance(result, AuthCodeResult)
        assert result.error is not None

    def test_auth_code_result_defaults(self) -> None:
        result = AuthCodeResult()
        assert result.code == ""
        assert result.state == ""
        assert result.error is None


# ---------------------------------------------------------------------------
# Credential storage (keyring mocked)
# ---------------------------------------------------------------------------


class TestKeychainStorage:
    def test_service_name(self) -> None:
        assert SERVICE_NAME == "code-assist"

    def test_store_credential(self) -> None:
        mock_keyring = MagicMock()
        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            assert store_credential("api_key", "sk-test") is True
            mock_keyring.set_password.assert_called_once_with(
                SERVICE_NAME, "api_key", "sk-test"
            )

    def test_get_credential(self) -> None:
        mock_keyring = MagicMock()
        mock_keyring.get_password.return_value = "sk-test"
        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            assert get_credential("api_key") == "sk-test"
            mock_keyring.get_password.assert_called_once_with(SERVICE_NAME, "api_key")

    def test_get_credential_missing(self) -> None:
        mock_keyring = MagicMock()
        mock_keyring.get_password.return_value = None
        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            assert get_credential("missing") is None

    def test_delete_credential(self) -> None:
        mock_keyring = MagicMock()
        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            assert delete_credential("api_key") is True
            mock_keyring.delete_password.assert_called_once_with(
                SERVICE_NAME, "api_key"
            )

    def test_store_credential_failure(self) -> None:
        mock_keyring = MagicMock()
        mock_keyring.set_password.side_effect = Exception("no keychain")
        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            assert store_credential("key", "val") is False

    def test_get_credential_failure(self) -> None:
        mock_keyring = MagicMock()
        mock_keyring.get_password.side_effect = Exception("no keychain")
        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            assert get_credential("key") is None

    def test_delete_credential_failure(self) -> None:
        mock_keyring = MagicMock()
        mock_keyring.delete_password.side_effect = Exception("no keychain")
        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            assert delete_credential("key") is False
