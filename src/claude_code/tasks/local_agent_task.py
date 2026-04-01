"""Background agent task management."""

from __future__ import annotations

from claude_code.tasks.types import Task, TaskStatus, TaskType, generate_task_id


def create_agent_task(
    description: str,
    *,
    agent_type: str = "custom",
) -> Task:
    """Create a background agent task."""
    return Task(
        task_id=generate_task_id(TaskType.LOCAL_AGENT),
        task_type=TaskType.LOCAL_AGENT,
        status=TaskStatus.PENDING,
        subject=description[:80],
        description=description,
        metadata={"agent_type": agent_type},
    )
