"""Async task store — in-process with watermark support for invalidation.

Watermark = an arbitrary string the task captured at submission time.
Use-case: simulation results are tagged with ``(portfolio_id, holdings_hash)``;
when the portfolio mutates, the router's current watermark diverges from
the stored one and the old result is marked ``stale_watermark=True`` so the
frontend can hide or warn about it.

Implementation is still single-process. Interfaces are shaped so it can be
replaced with Redis/Celery without changing callers.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional


logger = logging.getLogger(__name__)


@dataclass
class Task:
    id: str
    kind: str
    state: str = "pending"  # pending | running | succeeded | failed | cancelled
    progress: float = 0.0
    message: str = ""
    result: Any = None
    error_code: Optional[str] = None
    watermark: Optional[str] = None
    watermark_context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    def public(self, current_watermark: Optional[str] = None) -> Dict[str, Any]:
        stale = bool(
            self.watermark is not None
            and current_watermark is not None
            and self.watermark != current_watermark
        )
        return {
            "task_id": self.id,
            "id": self.id,
            "kind": self.kind,
            "state": self.state,
            "progress": round(self.progress, 3),
            "message": self.message,
            "result": self.result,
            "error": self.error_code,
            "error_code": self.error_code,
            "watermark": self.watermark,
            "watermark_context": self.watermark_context,
            "stale_watermark": stale,
            "created_at": self.created_at,
            "updated_at": self.finished_at or self.started_at or self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


class TaskStore:
    def __init__(self, max_tasks: int = 500) -> None:
        self._tasks: Dict[str, Task] = {}
        self._lock = asyncio.Lock()
        self._max = max_tasks

    def _gc(self) -> None:
        if len(self._tasks) <= self._max:
            return
        # Drop oldest terminal tasks first.
        by_age = sorted(self._tasks.values(), key=lambda t: t.created_at)
        for t in by_age:
            if t.state in ("succeeded", "failed", "cancelled"):
                self._tasks.pop(t.id, None)
            if len(self._tasks) <= self._max:
                break

    def create(self, kind: str, *, watermark: Optional[str] = None, watermark_context: Optional[Dict[str, Any]] = None) -> Task:
        task = Task(id=str(uuid.uuid4()), kind=kind, watermark=watermark, watermark_context=watermark_context or {})
        self._tasks[task.id] = task
        self._gc()
        return task

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def list(self, kind: Optional[str] = None) -> List[Task]:
        items = list(self._tasks.values())
        if kind:
            items = [t for t in items if t.kind == kind]
        items.sort(key=lambda t: t.created_at, reverse=True)
        return items

    async def run(
        self,
        kind: str,
        worker: Callable[[Task], Awaitable[Any]],
        *,
        watermark: Optional[str] = None,
        watermark_context: Optional[Dict[str, Any]] = None,
    ) -> Task:
        task = self.create(kind, watermark=watermark, watermark_context=watermark_context)

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


_STORE: Optional[TaskStore] = None


def get_task_store() -> TaskStore:
    global _STORE
    if _STORE is None:
        _STORE = TaskStore()
    return _STORE
