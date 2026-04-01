"""Cross-platform credential storage using keyring."""

import logging

logger = logging.getLogger(__name__)

SERVICE_NAME = "code-assist"


def store_credential(key: str, value: str) -> bool:
    """Store a credential in the system keychain."""
    try:
        import keyring

        keyring.set_password(SERVICE_NAME, key, value)
        return True
    except Exception as e:
        logger.warning("Failed to store credential: %s", e)
        return False


def get_credential(key: str) -> str | None:
    """Retrieve a credential from the system keychain."""
    try:
        import keyring

        return keyring.get_password(SERVICE_NAME, key)
    except Exception:
        return None


def delete_credential(key: str) -> bool:
    """Delete a credential from the system keychain."""
    try:
        import keyring

        keyring.delete_password(SERVICE_NAME, key)
        return True
    except Exception:
        return False
