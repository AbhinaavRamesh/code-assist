"""Built-in skill registration."""

from __future__ import annotations


def get_bundled_skills() -> list[dict]:
    """Get the list of bundled (built-in) skills."""
    return [
        {"name": "commit", "description": "Create a git commit"},
        {"name": "review-pr", "description": "Review a pull request"},
        {"name": "simplify", "description": "Review and simplify code"},
        {"name": "claude-api", "description": "Build apps with the Claude API"},
        {"name": "frontend-design", "description": "Create frontend interfaces"},
    ]
