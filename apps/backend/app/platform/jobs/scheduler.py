"""Simple asyncio background scheduler — no external deps."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("voxmetrik.scheduler")

_state: Dict[str, Any] = {
    "running": False,
    "run_count": 0,
    "last_run": None,
    "last_error": None,
    "last_results": [],
}

_task: Optional[asyncio.Task] = None


def get_scheduler_state() -> Dict[str, Any]:
    return dict(_state)


async def _run_jobs(jobs: List[Callable[[], dict]]) -> None:
    results = []
    for job in jobs:
        try:
            result = job()
            results.append({"job": job.__name__, "ok": True, "result": result})
        except Exception as exc:
            logger.error("job_failed job=%s error=%s", job.__name__, exc)
            results.append({"job": job.__name__, "ok": False, "error": str(exc)[:200]})
            _state["last_error"] = str(exc)[:200]
    _state["run_count"] = int(_state.get("run_count", 0)) + 1
    _state["last_run"] = datetime.now(timezone.utc).isoformat()
    _state["last_results"] = results[-5:]


async def _scheduler_loop(interval_sec: int, jobs: List[Callable[[], dict]]) -> None:
    _state["running"] = True
    logger.info("scheduler_started interval=%ss jobs=%s", interval_sec, len(jobs))
    try:
        while True:
            await _run_jobs(jobs)
            await asyncio.sleep(interval_sec)
    except asyncio.CancelledError:
        logger.info("scheduler_stopped")
        raise
    finally:
        _state["running"] = False


def start_scheduler(jobs: List[Callable[[], dict]]) -> None:
    global _task
    settings = get_settings()
    if not settings.jobs_enabled_effective:
        logger.info("scheduler_disabled")
        return
    if _task and not _task.done():
        return
    loop = asyncio.get_event_loop()
    from app.platform.realtime.hub import get_event_hub

    get_event_hub().bind_loop(loop)
    _task = loop.create_task(_scheduler_loop(settings.jobs_interval_sec, jobs))


async def stop_scheduler() -> None:
    global _task
    if _task and not _task.done():
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
    _task = None
