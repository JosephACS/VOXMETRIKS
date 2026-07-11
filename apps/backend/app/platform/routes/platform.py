"""Platform API — observability, notifications, realtime."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.packages.users.services.auth_deps import get_optional_user_id, require_engineer_user, require_user_id
from app.platform.notifications.service import get_notification_service
from app.platform.observability.status import PlatformStatusService
from app.platform.realtime.hub import get_event_hub

router = APIRouter(prefix="/platform", tags=["Platform"])


@router.get("/status", summary="Platform subsystem status")
def platform_status(_: int = Depends(require_engineer_user)):
    return PlatformStatusService().get_status()


@router.get("/metrics", summary="Basic platform metrics")
def platform_metrics(_: int = Depends(require_engineer_user)):
    return PlatformStatusService().get_metrics()


@router.get("/health/subsystems", summary="Public subsystem health summary")
def subsystems_health():
    """Lightweight health for dashboards — no stack traces."""
    status = PlatformStatusService().get_status()
    return {
        "warehouse": status["warehouse"].get("status", "unknown"),
        "recommendations": status["recommendations"].get("status", "unknown"),
        "audio_resolver": status["audio_resolver"].get("status", "unknown"),
        "jobs": "running" if status["jobs"].get("running") else "idle",
        "realtime": status["realtime"].get("mode", "polling"),
    }


@router.get("/notifications", summary="User notifications")
def list_notifications(
    user_id: int = Depends(require_user_id),
    limit: int = Query(30, ge=1, le=100),
):
    return {"notifications": get_notification_service().list_for_user(user_id, limit=limit)}


@router.get("/events", summary="SSE event stream")
async def sse_events(user_id: Optional[int] = Depends(get_optional_user_id)):
    settings = get_settings()
    if not settings.sse_enabled:
        return {"mode": "polling", "poll_url": "/api/v1/platform/notifications"}

    async def _gen():
        async for chunk in get_event_hub().stream(user_id):
            yield chunk

    return StreamingResponse(_gen(), media_type="text/event-stream")
