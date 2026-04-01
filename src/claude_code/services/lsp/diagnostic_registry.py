"""LSP diagnostic tracking and registry."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Diagnostic:
    """A single LSP diagnostic."""

    file_path: str = ""
    line: int = 0
    column: int = 0
    severity: int = 1  # 1=Error, 2=Warning, 3=Info, 4=Hint
    message: str = ""
    source: str = ""
    code: str | int | None = None

    @property
    def severity_label(self) -> str:
        return {1: "Error", 2: "Warning", 3: "Info", 4: "Hint"}.get(
            self.severity, "Unknown"
        )


class DiagnosticRegistry:
    """Tracks LSP diagnostics across files."""

    def __init__(self) -> None:
        self._diagnostics: dict[str, list[Diagnostic]] = {}

    def update(self, file_path: str, diagnostics: list[Diagnostic]) -> None:
        """Update diagnostics for a file (replaces all previous)."""
        if diagnostics:
            self._diagnostics[file_path] = diagnostics
        else:
            self._diagnostics.pop(file_path, None)

    def get(self, file_path: str) -> list[Diagnostic]:
        """Get diagnostics for a file."""
        return self._diagnostics.get(file_path, [])

    def get_all(self) -> dict[str, list[Diagnostic]]:
        """Get all diagnostics grouped by file."""
        return dict(self._diagnostics)

    def get_errors(self, file_path: str | None = None) -> list[Diagnostic]:
        """Get only error-severity diagnostics."""
        if file_path:
            return [d for d in self.get(file_path) if d.severity == 1]
        return [
            d
            for diags in self._diagnostics.values()
            for d in diags
            if d.severity == 1
        ]

    def clear(self, file_path: str | None = None) -> None:
        """Clear diagnostics for a file or all files."""
        if file_path:
            self._diagnostics.pop(file_path, None)
        else:
            self._diagnostics.clear()

    @property
    def total_count(self) -> int:
        return sum(len(d) for d in self._diagnostics.values())

    @property
    def error_count(self) -> int:
        return len(self.get_errors())
