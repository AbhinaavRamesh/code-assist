"""Session cost tracking.

Ports the TypeScript cost tracker from src/cost-tracker.ts.
"""

from __future__ import annotations

from code_assist.state.bootstrap import get_bootstrap_state
from code_assist.types.message import ModelUsage, Usage
from code_assist.utils.model.cost import calculate_cost_usd


def track_usage(model: str, usage: Usage) -> float:
    """Track token usage and return the cost in USD."""
    cost = calculate_cost_usd(
        model,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_read_tokens=usage.cache_read_input_tokens,
        cache_creation_tokens=usage.cache_creation_input_tokens,
    )

    state = get_bootstrap_state()
    state.add_cost(cost)

    # Update per-model usage
    if model not in state.model_usage:
        state.model_usage[model] = ModelUsage()
    mu = state.model_usage[model]
    mu.input_tokens += usage.input_tokens
    mu.output_tokens += usage.output_tokens
    mu.cache_read_input_tokens += usage.cache_read_input_tokens
    mu.cache_creation_input_tokens += usage.cache_creation_input_tokens
    mu.cost_usd += cost

    return cost


def get_total_cost_usd() -> float:
    """Get the total session cost in USD."""
    return get_bootstrap_state().total_cost_usd


def get_model_usage() -> dict[str, ModelUsage]:
    """Get per-model usage breakdown."""
    return get_bootstrap_state().model_usage


def format_cost(cost_usd: float) -> str:
    """Format a cost value for display."""
    if cost_usd < 0.01:
        return f"${cost_usd:.4f}"
    return f"${cost_usd:.2f}"
