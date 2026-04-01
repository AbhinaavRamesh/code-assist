"""File utility functions.

Provides path resolution, binary detection, file size, and similar-file suggestions.
"""

from __future__ import annotations

import os
from pathlib import Path


def expand_path(path: str, cwd: str) -> str:
    """Resolve ``~`` and relative paths against *cwd*.

    Returns an absolute, normalised path string.
    """
    expanded = os.path.expanduser(path)
    if not os.path.isabs(expanded):
        expanded = os.path.join(cwd, expanded)
    return os.path.normpath(expanded)


# Byte values that are never valid in text files (C0 controls except common
# whitespace characters: TAB, LF, CR).
_BINARY_BYTES = set(range(0, 8)) | {11} | set(range(14, 32))


def is_binary_file(path: str, *, sample_size: int = 8192) -> bool:
    """Heuristic check for binary content.

    Reads the first *sample_size* bytes and looks for non-text control
    characters.  Returns ``True`` when binary bytes are found or the file
    cannot be read.
    """
    try:
        with open(path, "rb") as f:
            chunk = f.read(sample_size)
        if not chunk:
            return False
        return bool(_BINARY_BYTES & set(chunk))
    except OSError:
        return True


def get_file_size(path: str) -> int:
    """Return the size of *path* in bytes.

    Raises ``FileNotFoundError`` if *path* does not exist.
    """
    return os.path.getsize(path)


def suggest_similar_files(path: str, cwd: str, *, max_results: int = 5) -> list[str]:
    """Suggest similarly-named files when *path* does not exist.

    Searches the directory of *path* (falling back to *cwd*) for files whose
    names share a common prefix or substring with the basename of *path*.
    Returns up to *max_results* suggestions sorted by similarity.
    """
    target = os.path.basename(path)
    search_dir = os.path.dirname(expand_path(path, cwd)) or cwd

    if not os.path.isdir(search_dir):
        return []

    try:
        entries = os.listdir(search_dir)
    except OSError:
        return []

    target_lower = target.lower()
    scored: list[tuple[float, str]] = []

    for entry in entries:
        entry_lower = entry.lower()
        # Simple similarity: longest common substring ratio
        score = _lcs_ratio(target_lower, entry_lower)
        if score > 0.3:
            full = os.path.join(search_dir, entry)
            scored.append((score, full))

    scored.sort(key=lambda t: t[0], reverse=True)
    return [s[1] for s in scored[:max_results]]


def _lcs_ratio(a: str, b: str) -> float:
    """Longest common substring length divided by max string length."""
    if not a or not b:
        return 0.0
    m = len(a)
    n = len(b)
    longest = 0
    prev = [0] * (n + 1)
    for i in range(m):
        curr = [0] * (n + 1)
        for j in range(n):
            if a[i] == b[j]:
                curr[j + 1] = prev[j] + 1
                if curr[j + 1] > longest:
                    longest = curr[j + 1]
        prev = curr
    return longest / max(m, n)
