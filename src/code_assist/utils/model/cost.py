"""Per-model token pricing and cost calculation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelPricing:
    """Pricing per million tokens for a model."""

    input_per_mtok: float  # $ per 1M input tokens
    output_per_mtok: float  # $ per 1M output tokens
    cache_read_per_mtok: float  # $ per 1M cache read tokens
    cache_write_per_mtok: float  # $ per 1M cache write tokens
    context_window: int  # max context window size
    max_output: int  # max output tokens


# Pricing table (as of 2025)
MODEL_PRICING: dict[str, ModelPricing] = {
    # Claude 4.6
    "claude-opus-4-6": ModelPricing(
        input_per_mtok=15.0,
        output_per_mtok=75.0,
        cache_read_per_mtok=1.5,
        cache_write_per_mtok=18.75,
        context_window=1_000_000,
        max_output=32768,
    ),
    "claude-sonnet-4-6": ModelPricing(
        input_per_mtok=3.0,
        output_per_mtok=15.0,
        cache_read_per_mtok=0.3,
        cache_write_per_mtok=3.75,
        context_window=1_000_000,
        max_output=16384,
    ),
    # Claude 4
    "claude-opus-4-20250514": ModelPricing(
        input_per_mtok=15.0,
        output_per_mtok=75.0,
        cache_read_per_mtok=1.5,
        cache_write_per_mtok=18.75,
        context_window=200_000,
        max_output=32768,
    ),
    "claude-sonnet-4-20250514": ModelPricing(
        input_per_mtok=3.0,
        output_per_mtok=15.0,
        cache_read_per_mtok=0.3,
        cache_write_per_mtok=3.75,
        context_window=200_000,
        max_output=16384,
    ),
    # Claude 3.5
    "claude-haiku-3-5-20241022": ModelPricing(
        input_per_mtok=0.8,
        output_per_mtok=4.0,
        cache_read_per_mtok=0.08,
        cache_write_per_mtok=1.0,
        context_window=200_000,
        max_output=8192,
    ),
    "claude-haiku-4-5-20251001": ModelPricing(
        input_per_mtok=0.8,
        output_per_mtok=4.0,
        cache_read_per_mtok=0.08,
        cache_write_per_mtok=1.0,
        context_window=200_000,
        max_output=8192,
    ),
}

# Default pricing for unknown models
_DEFAULT_PRICING = ModelPricing(
    input_per_mtok=3.0,
    output_per_mtok=15.0,
    cache_read_per_mtok=0.3,
    cache_write_per_mtok=3.75,
    context_window=200_000,
    max_output=16384,
)


def get_pricing(model: str) -> ModelPricing:
    """Get pricing for a model. Falls back to default if unknown."""
    return MODEL_PRICING.get(model, _DEFAULT_PRICING)


def calculate_cost_usd(
    model: str,
    *,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_read_tokens: int = 0,
    cache_creation_tokens: int = 0,
) -> float:
    """Calculate the USD cost for a given token usage."""
    pricing = get_pricing(model)
    cost = (
        (input_tokens / 1_000_000) * pricing.input_per_mtok
        + (output_tokens / 1_000_000) * pricing.output_per_mtok
        + (cache_read_tokens / 1_000_000) * pricing.cache_read_per_mtok
        + (cache_creation_tokens / 1_000_000) * pricing.cache_write_per_mtok
    )
    return cost


def get_context_window(model: str) -> int:
    """Get the context window size for a model."""
    return get_pricing(model).context_window


def get_max_output_tokens(model: str) -> int:
    """Get the max output tokens for a model."""
    return get_pricing(model).max_output
