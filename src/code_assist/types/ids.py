"""Branded ID types for type-safe identifiers."""

from __future__ import annotations

import re
import uuid
from typing import NewType

# Branded string types for session and agent IDs
SessionId = NewType("SessionId", str)
AgentId = NewType("AgentId", str)
RequestId = NewType("RequestId", str)

# Pattern: 'a' + optional '<label>-' + 16 hex chars
_AGENT_ID_PATTERN = re.compile(r"^a(?:.+-)?[0-9a-f]{16}$")


def as_session_id(id_str: str) -> SessionId:
    """Cast a string to SessionId."""
    return SessionId(id_str)


def as_agent_id(id_str: str) -> AgentId:
    """Cast a string to AgentId."""
    return AgentId(id_str)


def to_agent_id(s: str) -> AgentId | None:
    """Validate and brand a string as AgentId. Returns None if invalid."""
    if _AGENT_ID_PATTERN.match(s):
        return AgentId(s)
    return None


def generate_session_id() -> SessionId:
    """Generate a new unique session ID."""
    return SessionId(uuid.uuid4().hex)


def generate_agent_id(label: str | None = None) -> AgentId:
    """Generate a new agent ID with optional label prefix."""
    hex_suffix = uuid.uuid4().hex[:16]
    if label:
        return AgentId(f"a{label}-{hex_suffix}")
    return AgentId(f"a{hex_suffix}")
