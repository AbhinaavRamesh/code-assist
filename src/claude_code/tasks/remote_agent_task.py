"""Remote agent task communication."""

from __future__ import annotations

from claude_code.tasks.types import Task, TaskStatus, TaskType, generate_task_id


def create_remote_task(
    description: str,
    *,
    session_url: str = "",
) -> Task:
    """Create a remote agent task."""
    return Task(
        task_id=generate_task_id(TaskType.REMOTE_AGENT),
        task_type=TaskType.REMOTE_AGENT,
        status=TaskStatus.PENDING,
        subject=description[:80],
        description=description,
        metadata={"session_url": session_url},
    )
