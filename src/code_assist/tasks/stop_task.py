"""Task cancellation."""

from __future__ import annotations

import logging
import os
import signal

from code_assist.tasks.types import Task, TaskStatus

logger = logging.getLogger(__name__)


def stop_task(task: Task) -> bool:
    """Attempt to stop a running task."""
    if task.status != TaskStatus.RUNNING:
        return False

    pid = task.metadata.get("pid")
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            task.status = TaskStatus.KILLED
            return True
        except ProcessLookupError:
            task.status = TaskStatus.KILLED
            return True
        except Exception as e:
            logger.warning("Failed to kill task %s: %s", task.task_id, e)
            return False

    task.status = TaskStatus.KILLED
    return True
