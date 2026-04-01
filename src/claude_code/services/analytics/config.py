"""Analytics configuration."""

import os


def is_analytics_enabled() -> bool:
    """Check if analytics collection is enabled."""
    return os.environ.get("CODE_ASSIST_DISABLE_ANALYTICS", "").lower() not in ("1", "true")


def get_analytics_endpoint() -> str:
    """Get the analytics endpoint URL."""
    return os.environ.get("CODE_ASSIST_ANALYTICS_URL", "")
