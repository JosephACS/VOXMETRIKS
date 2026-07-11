"""Background maintenance tasks — non-blocking, lightweight."""

from __future__ import annotations

from app.core.cache import cache_invalidate
from app.core.logging import get_logger
from app.platform.notifications.service import get_notification_service

logger = get_logger("voxmetrik.jobs")


def task_refresh_recommendations_cache() -> dict:
    removed = cache_invalidate("smart")
    removed += cache_invalidate("recommendations")
    logger.info("job_refresh_recommendations removed=%s", removed)
    return {"cache_invalidated": removed}


def task_clean_stale_cache() -> dict:
    removed = cache_invalidate(None)
    logger.info("job_clean_cache removed=%s", removed)
    return {"cache_cleared": removed}


def task_validate_audio_sources() -> dict:
    """Placeholder probe — full validation runs on-demand via audio resolver."""
    logger.info("job_validate_audio tick")
    return {"status": "ok", "note": "on-demand resolver validation"}


def task_record_metrics() -> dict:
    from app.platform.observability.status import PlatformStatusService

    metrics = PlatformStatusService().get_metrics()
    logger.info("job_metrics %s", metrics)
    return metrics
