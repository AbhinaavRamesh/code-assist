"""File state cache with LRU eviction.

Tracks file modification times and content hashes to detect changes
without re-reading entire files.
"""

from __future__ import annotations

import hashlib
import os
from collections import OrderedDict
from dataclasses import dataclass


@dataclass(slots=True)
class _CacheEntry:
    """Internal cache entry."""

    mtime: float
    size: int
    content_hash: str


class FileStateCache:
    """LRU cache mapping file paths to modification metadata.

    Parameters
    ----------
    max_size:
        Maximum number of entries before the least-recently-used entry is
        evicted.
    """

    def __init__(self, max_size: int = 4096) -> None:
        self._max_size = max_size
        self._store: OrderedDict[str, _CacheEntry] = OrderedDict()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, path: str) -> _CacheEntry | None:
        """Get the cached entry for *path*, promoting it in the LRU order."""
        entry = self._store.get(path)
        if entry is not None:
            self._store.move_to_end(path)
        return entry

    def is_stale(self, path: str) -> bool:
        """Return ``True`` if the file has changed since it was cached."""
        entry = self.get(path)
        if entry is None:
            return True
        try:
            stat = os.stat(path)
        except OSError:
            return True
        return stat.st_mtime != entry.mtime or stat.st_size != entry.size

    def update(self, path: str, *, content: bytes | None = None) -> str:
        """Update the cache for *path* and return the content hash.

        If *content* is ``None`` the file is read from disk.
        """
        if content is None:
            with open(path, "rb") as f:
                content = f.read()

        stat = os.stat(path)
        content_hash = hashlib.sha256(content).hexdigest()
        entry = _CacheEntry(
            mtime=stat.st_mtime,
            size=stat.st_size,
            content_hash=content_hash,
        )

        self._store[path] = entry
        self._store.move_to_end(path)
        self._evict()
        return content_hash

    def invalidate(self, path: str) -> None:
        """Remove *path* from the cache."""
        self._store.pop(path, None)

    def clear(self) -> None:
        """Remove all entries."""
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, path: str) -> bool:
        return path in self._store

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _evict(self) -> None:
        while len(self._store) > self._max_size:
            self._store.popitem(last=False)
