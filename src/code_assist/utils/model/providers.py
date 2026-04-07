"""API provider detection and configuration."""

from __future__ import annotations

import os
from enum import StrEnum


class APIProvider(StrEnum):
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"


def detect_provider() -> APIProvider:
    """Detect which API provider to use based on environment."""
    if os.environ.get("AWS_REGION") or os.environ.get("ANTHROPIC_BEDROCK_BASE_URL"):
        return APIProvider.BEDROCK
    if os.environ.get("CLOUD_ML_REGION") or os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID"):
        return APIProvider.VERTEX
    return APIProvider.ANTHROPIC


def get_base_url(provider: APIProvider | None = None) -> str | None:
    """Get the API base URL for a provider."""
    # Custom base URL always takes precedence
    custom = os.environ.get("ANTHROPIC_BASE_URL")
    if custom:
        return custom

    if provider == APIProvider.BEDROCK:
        return os.environ.get("ANTHROPIC_BEDROCK_BASE_URL")
    if provider == APIProvider.VERTEX:
        return os.environ.get("ANTHROPIC_VERTEX_BASE_URL")

    return None
