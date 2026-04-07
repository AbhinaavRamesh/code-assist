"""Model name resolution and canonical names."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Model Families & Canonical Names
# ---------------------------------------------------------------------------

# Model ID -> display name
MODEL_DISPLAY_NAMES: dict[str, str] = {
    "claude-opus-4-20250514": "Opus 4",
    "claude-sonnet-4-20250514": "Sonnet 4",
    "claude-haiku-3-5-20241022": "Haiku 3.5",
    "claude-opus-4-6": "Opus 4.6",
    "claude-sonnet-4-6": "Sonnet 4.6",
    "claude-haiku-4-5-20251001": "Haiku 4.5",
}

# Shorthand aliases
MODEL_ALIASES: dict[str, str] = {
    "opus": "claude-opus-4-6",
    "sonnet": "claude-sonnet-4-6",
    "haiku": "claude-haiku-4-5-20251001",
    "opus-4": "claude-opus-4-20250514",
    "sonnet-4": "claude-sonnet-4-20250514",
    "opus-4.6": "claude-opus-4-6",
    "sonnet-4.6": "claude-sonnet-4-6",
    "haiku-4.5": "claude-haiku-4-5-20251001",
}

DEFAULT_MODEL = "claude-sonnet-4-6"


def resolve_model(model_str: str) -> str:
    """Resolve a model string to its canonical model ID."""
    return MODEL_ALIASES.get(model_str, model_str)


def get_display_name(model: str) -> str:
    """Get a human-readable display name for a model."""
    return MODEL_DISPLAY_NAMES.get(model, model)


def is_opus_model(model: str) -> bool:
    """Check if a model is an Opus variant."""
    return "opus" in model.lower()


def is_haiku_model(model: str) -> bool:
    """Check if a model is a Haiku variant."""
    return "haiku" in model.lower()


def is_sonnet_model(model: str) -> bool:
    """Check if a model is a Sonnet variant."""
    return "sonnet" in model.lower()
