"""Token counting and estimation utilities."""

from __future__ import annotations


def rough_token_estimate(text: str) -> int:
    """Rough estimate of token count from text.

    Uses the ~4 chars per token heuristic.
    """
    return max(1, len(text) // 4)


def estimate_message_tokens(messages: list[dict]) -> int:
    """Estimate total tokens in a list of messages."""
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += rough_token_estimate(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text", "")
                    if text:
                        total += rough_token_estimate(text)
                    # Tool use inputs add tokens
                    inp = block.get("input", {})
                    if inp:
                        import json
                        total += rough_token_estimate(json.dumps(inp))
    return total
