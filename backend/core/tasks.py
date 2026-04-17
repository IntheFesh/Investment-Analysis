"""In-process async task store.

This is a minimal but structurally-correct implementation of the product
spec's task_id contract: long-running endpoints return a task id, the
front-end polls status, and results are fetched when ``state == "succeeded"``.

The store is in-memory and single-process — fine for a local / demo
environment. Swap ``TaskStore`` with a Celery/RQ-backed version later.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Optional


logger = logging.getLogger(__name__)


@dataclass
class Task:
    id: str
    kind: str
    state: str = "pending"  # pending | running | succeeded | failed
    progress: float = 0.0
    message: str = ""
    result: Any = None
    error_code: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    def public(self) -> Dict[str, Any]:
        return {
            "task_id": self.id,
            "kind": self.kind,
            "state": self.state,
            "progress": round(self.progress, 3),
            "message": self.message,
            "result": self.result,
            "error_code": self.error_code,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


class TaskStore:
    def __init__(self) -> None:
        self._tasks: Dict[str, Task] = {}
        self._lock = asyncio.Lock()

    def create(self, kind: str) -> Task:
        task = Task(id=str(uuid.uuid4()), kind=kind)
        self._tasks[task.id] = task
        return task

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def list(self, kind: Optional[str] = None) -> list[Task]:
        items = list(self._tasks.values())
        if kind:
            items = [t for t in items if t.kind == kind]
        items.sort(key=lambda t: t.created_at, reverse=True)
        return items

    async def run(
        self,
        kind: str,
        worker: Callable[[Task], Awaitable[Any]],
    ) -> Task:
        task = self.create(kind)

        async def _runner() -> None:
            task.state = "running"
            task.started_at = datetime.now(tz=timezone.utc).isoformat()
            try:
                result = await worker(task)
                task.result = result
                task.progress = 1.0
                task.state = "succeeded"
                task.message = "ok"
            except Exception as exc:  # noqa: BLE001
                logger.exception("task %s failed", task.id)
                task.state = "failed"
                task.error_code = "TASK_FAILED"
                task.message = str(exc)
            finally:
                task.finished_at = datetime.now(tz=timezone.utc).isoformat()

        asyncio.create_task(_runner())
        return task


_STORE: TaskStore | None = None


def get_task_store() -> TaskStore:
    global _STORE
    if _STORE is None:
        _STORE = TaskStore()
    return _STORE
