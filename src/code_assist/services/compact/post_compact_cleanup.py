"""Cleanup after compaction - file state cache, etc."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def post_compact_cleanup(
    file_state_cache: dict | None = None,
) -> None:
    """Perform cleanup after conversation compaction.

    Clears file state cache since compacted messages may have
    referenced files that are no longer in context.
    """
    if file_state_cache is not None:
        file_state_cache.clear()
        logger.debug("Cleared file state cache after compaction")
