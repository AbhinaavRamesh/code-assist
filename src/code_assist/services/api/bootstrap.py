"""Bootstrap data fetching for API initialization."""

from __future__ import annotations

from typing import Any


async def fetch_bootstrap_data(
    api_key: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Fetch bootstrap data from the API.

    This includes model availability, feature flags, etc.
    Returns empty dict if unavailable.
    """
    # Placeholder - full implementation in later branches
    return {}
