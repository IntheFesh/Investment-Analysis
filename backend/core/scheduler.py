"""Trading-day scheduler skeleton.

This is an honest skeleton: it defines the shape of a production refresh
pipeline without pretending to run one. Real deployments will register
refresh callables against the scheduler; the CLI/container host decides
whether to tick forward on every trading day.

Loop shape
----------
Each tick we:
1. Ask the calendar whether today is a trading day for the target region.
2. Walk through registered ``Job`` objects in declared order; each job
   declares the upstream state it needs so dependencies are linearised.
3. Invalidate the relevant ``SnapshotCache`` namespaces.
4. Record job outcome (ok / degraded / failed) and a ``last_run_at``.

Defaults
--------
The scheduler starts empty so importing it does not silently kick off
work. Applications attach refresh jobs via :func:`register_default_jobs`
or by constructing ``JobSpec`` entries directly.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Callable, Dict, List, Optional

from .calendar import is_trading_day, last_trading_day
from .snapshot_cache import hot_cache, warm_cache


logger = logging.getLogger(__name__)


JobFn = Callable[[], None]


@dataclass
class JobSpec:
    name: str
    fn: JobFn
    depends_on: List[str] = field(default_factory=list)
    cache_namespaces: List[str] = field(default_factory=list)
    region: str = "CN"
    description: str = ""


@dataclass
class JobRun:
    name: str
    status: str = "idle"              # idle | ok | degraded | failed
    last_run_at: Optional[str] = None
    last_error: Optional[str] = None
    duration_ms: Optional[float] = None


class TradingDayScheduler:
    """In-process scheduler skeleton with observable state."""

    def __init__(self) -> None:
        self._jobs: List[JobSpec] = []
        self._state: Dict[str, JobRun] = {}
        self._lock = threading.Lock()

    def register(self, spec: JobSpec) -> None:
        with self._lock:
            self._jobs.append(spec)
            self._state.setdefault(spec.name, JobRun(name=spec.name))

    def jobs(self) -> List[JobSpec]:
        with self._lock:
            return list(self._jobs)

    def status(self) -> List[JobRun]:
        with self._lock:
            return list(self._state.values())

    def tick(self, today: Optional[date] = None, *, force: bool = False) -> Dict[str, JobRun]:
        """Run one scheduler tick. ``force=True`` ignores the trading-day gate."""
        today = today or datetime.utcnow().date()
        results: Dict[str, JobRun] = {}

        regions = {spec.region for spec in self._jobs}
        if not force:
            active_regions = {r for r in regions if is_trading_day(today, region=r)}
            if not active_regions:
                return results

        for spec in self._jobs:
            if not force and not is_trading_day(today, region=spec.region):
                continue
            run = self._execute(spec)
            results[spec.name] = run
        return results

    def _execute(self, spec: JobSpec) -> JobRun:
        start = datetime.now(tz=timezone.utc)
        run = self._state.setdefault(spec.name, JobRun(name=spec.name))
        try:
            spec.fn()
            status = "ok"
            err = None
        except Exception as exc:  # noqa: BLE001
            logger.exception("scheduler job %s failed", spec.name)
            status = "failed"
            err = f"{type(exc).__name__}: {exc}"

        duration_ms = (datetime.now(tz=timezone.utc) - start).total_seconds() * 1000
        run.status = status
        run.last_error = err
        run.last_run_at = start.isoformat()
        run.duration_ms = round(duration_ms, 2)

        for ns in spec.cache_namespaces:
            hot_cache().invalidate_prefix(ns)
            warm_cache().invalidate_prefix(ns)

        return run


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------


_scheduler: Optional[TradingDayScheduler] = None
_scheduler_lock = threading.Lock()


def get_scheduler() -> TradingDayScheduler:
    global _scheduler
    with _scheduler_lock:
        if _scheduler is None:
            _scheduler = TradingDayScheduler()
        return _scheduler


def register_default_jobs() -> None:
    """Idempotently register the baseline refresh jobs.

    Each registered job invalidates its cache namespace. The actual data
    recomputation runs on the next request because handlers call
    ``hot_cache().get(..., rebuild=fn)`` which rebuilds on miss.
    """
    sched = get_scheduler()
    existing = {j.name for j in sched.jobs()}

    def _mark(ns: str) -> JobFn:
        def _fn() -> None:
            hot_cache().invalidate_prefix(ns)
            warm_cache().invalidate_prefix(ns)
        return _fn

    plan = [
        JobSpec("market_overview", _mark("market:"), cache_namespaces=["market:"], description="重置市场概览快照"),
        JobSpec(
            "sentiment_factors", _mark("sentiment:"),
            depends_on=["market_overview"], cache_namespaces=["sentiment:"],
            description="重置情绪四因子快照",
        ),
        JobSpec(
            "portfolio_snapshots", _mark("portfolio:"),
            depends_on=["sentiment_factors"], cache_namespaces=["portfolio:"],
            description="使组合概览 & 诊断缓存失效（按需重算）",
        ),
    ]
    for spec in plan:
        if spec.name not in existing:
            sched.register(spec)


def last_trading_day_iso(region: str = "CN") -> str:
    return last_trading_day(region).isoformat()
