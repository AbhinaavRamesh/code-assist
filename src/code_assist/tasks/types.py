"""Task management types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class TaskType(StrEnum):
    LOCAL_BASH = "local_bash"
    LOCAL_AGENT = "local_agent"
    REMOTE_AGENT = "remote_agent"
    IN_PROCESS_TEAMMATE = "in_process_teammate"
    LOCAL_WORKFLOW = "local_workflow"
    MONITOR_MCP = "monitor_mcp"
    DREAM = "dream"


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"


# Task ID prefixes by type
TASK_ID_PREFIXES = {
    TaskType.LOCAL_BASH: "b",
    TaskType.LOCAL_AGENT: "a",
    TaskType.REMOTE_AGENT: "r",
    TaskType.IN_PROCESS_TEAMMATE: "t",
    TaskType.LOCAL_WORKFLOW: "w",
    TaskType.MONITOR_MCP: "m",
    TaskType.DREAM: "d",
}


@dataclass
class Task:
    """A background task."""

    task_id: str = ""
    task_type: TaskType = TaskType.LOCAL_BASH
    status: TaskStatus = TaskStatus.PENDING
    subject: str = ""
    description: str = ""
    active_form: str | None = None
    owner: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    blocks: list[str] = field(default_factory=list)
    blocked_by: list[str] = field(default_factory=list)
    output_file: str | None = None
    created_at: float = 0.0
    updated_at: float = 0.0


def generate_task_id(task_type: TaskType) -> str:
    """Generate a unique task ID with type prefix."""
    import uuid

    prefix = TASK_ID_PREFIXES.get(task_type, "x")
    return f"{prefix}-{uuid.uuid4().hex[:8]}"
