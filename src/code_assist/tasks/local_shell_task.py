"""Background shell task management."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from code_assist.tasks.types import Task, TaskStatus, TaskType, generate_task_id

logger = logging.getLogger(__name__)


async def spawn_shell_task(
    command: str,
    *,
    description: str = "",
    cwd: str | None = None,
) -> Task:
    """Spawn a background shell task."""
    task = Task(
        task_id=generate_task_id(TaskType.LOCAL_BASH),
        task_type=TaskType.LOCAL_BASH,
        status=TaskStatus.RUNNING,
        subject=description or command[:50],
        description=description,
    )

    # Start subprocess in background
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        task.metadata["pid"] = proc.pid
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.metadata["error"] = str(e)

    return task
