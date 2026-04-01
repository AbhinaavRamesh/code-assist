"""Context window management utilities."""

from __future__ import annotations

from code_assist.utils.model.cost import get_context_window, get_max_output_tokens


def get_available_tokens(model: str, *, used_tokens: int = 0) -> int:
    """Get the number of tokens available for new content."""
    window = get_context_window(model)
    max_output = get_max_output_tokens(model)
    # Reserve space for output + buffer
    return max(0, window - max_output - used_tokens)


def should_compact(model: str, *, used_tokens: int) -> bool:
    """Check if conversation should be compacted."""
    window = get_context_window(model)
    # Compact when using more than 80% of context
    threshold = int(window * 0.8)
    return used_tokens > threshold
