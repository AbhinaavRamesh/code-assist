"""Finding relevant memories for context injection."""

from __future__ import annotations

from code_assist.memory.memory_scan import scan_memory_files
from code_assist.memory.memory_types import MemoryEntry


def find_relevant_memories(
    project_root: str, query: str
) -> list[MemoryEntry]:
    """Find memories relevant to a query via simple keyword matching."""
    entries = scan_memory_files(project_root)
    if not query:
        return entries

    query_lower = query.lower()
    keywords = query_lower.split()

    scored: list[tuple[int, MemoryEntry]] = []
    for entry in entries:
        searchable = f"{entry.name} {entry.description} {entry.content}".lower()
        score = sum(1 for kw in keywords if kw in searchable)
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in scored]


def should_load_memory(entry: MemoryEntry, context: str) -> bool:
    """Check if a memory entry should be loaded for the given context."""
    if not entry.description:
        return True
    context_lower = context.lower()
    desc_words = entry.description.lower().split()
    return any(word in context_lower for word in desc_words if len(word) > 3)
