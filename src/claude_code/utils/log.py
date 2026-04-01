"""Logging setup for code-assist."""

from __future__ import annotations

import logging
import sys


def setup_logging(*, verbose: bool = False, debug: bool = False) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s", datefmt="%H:%M:%S")
    )

    root = logging.getLogger("claude_code")
    root.setLevel(level)
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module."""
    return logging.getLogger(f"code_assist.{name}")
