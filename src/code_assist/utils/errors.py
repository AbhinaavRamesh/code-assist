"""Base error types for code-assist."""

from __future__ import annotations


class CodeAssistError(Exception):
    """Base error for all code-assist errors."""


class ConfigError(CodeAssistError):
    """Error in configuration loading or validation."""


class AuthError(CodeAssistError):
    """Authentication error."""


class APIError(CodeAssistError):
    """Error communicating with the API."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class PromptTooLongError(APIError):
    """Prompt exceeds the model's context window."""


class RateLimitError(APIError):
    """API rate limit exceeded."""


class OverloadedError(APIError):
    """API is overloaded."""


class ToolError(CodeAssistError):
    """Error during tool execution."""


class PermissionError_(CodeAssistError):
    """Permission denied for a tool operation."""


class SessionError(CodeAssistError):
    """Error with session management."""
