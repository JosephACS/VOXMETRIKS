"""Aggregate subsystem health for enterprise observability."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from app.core.cache import cache_stats
from app.core.config import get_settings
from app.platform.jobs.scheduler import get_scheduler_state
from app.platform.notifications.store import get_notification_store
from app.services.health_service import HealthService


class PlatformStatusService:
    """Unified platform status — warehouse, cache, jobs, subsystems."""

    def get_status(self) -> Dict[str, Any]:
        settings = get_settings()
        warehouse = self._warehouse_status()
        cache = cache_stats()
        jobs = get_scheduler_state()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": settings.environment,
            "warehouse": warehouse,
            "cache": cache,
            "playback": {"status": "ok", "note": "client-side Phase 1–2 engine"},
            "audio_resolver": self._audio_resolver_status(),
            "recommendations": self._recommendations_status(cache),
            "jobs": jobs,
            "notifications": {"stored": get_notification_store().count()},
            "realtime": {
                "mode": "sse" if settings.sse_enabled else "polling",
                "sse_endpoint": "/api/v1/platform/events" if settings.sse_enabled else None,
            },
        }

    def get_metrics(self) -> Dict[str, Any]:
        cache = cache_stats()
        return {
            "cache_entries": cache.get("entries", 0),
            "cache_enabled": cache.get("enabled", False),
            "notifications_total": get_notification_store().count(),
            "jobs_runs": get_scheduler_state().get("run_count", 0),
        }

    def _warehouse_status(self) -> Dict[str, Any]:
        try:
            health = HealthService().get_system_health()
            return {
                "status": health.status,
                "db_connected": health.db_connected,
                "tables_ok": health.tables_ok,
                "gold_ready": health.gold_ready,
                "etl_status": health.etl_status,
            }
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)[:200]}

    def _audio_resolver_status(self) -> Dict[str, Any]:
        settings = get_settings()
        return {
            "status": "ok",
            "youtube_configured": bool(settings.youtube_api_key.strip()),
            "providers": ["youtube", "audius", "demo"],
            "cache_domain": "audio_resolver",
        }

    def _recommendations_status(self, cache: Dict[str, Any]) -> Dict[str, Any]:
        prefixes = cache.get("prefixes", {})
        smart_keys = sum(v for k, v in prefixes.items() if "smart" in k or "recommend" in k)
        return {
            "status": "ok",
            "engine": "hybrid_phase4",
            "cached_smart_entries": smart_keys,
        }
