"""Tests for Enterprise Platform — Phase 5."""

from app.core.cache import cache_set, cache_get, cache_stats, cache_invalidate
from app.platform.notifications.service import get_notification_service
from app.platform.notifications.models import NotificationKind
from app.platform.observability.status import PlatformStatusService


def test_cache_stats_tracks_entries():
    cache_invalidate(None)
    cache_set("test:key", {"ok": True}, 60)
    stats = cache_stats()
    assert stats["enabled"] is True
    assert stats["entries"] >= 1
    cache_invalidate("test")


def test_notification_emit():
    svc = get_notification_service()
    note = svc.emit(NotificationKind.SYSTEM, "Test", "Message", user_id=1)
    assert note.title == "Test"
    items = svc.list_for_user(1, limit=5)
    assert any(i["id"] == note.id for i in items)


def test_platform_status_shape():
    status = PlatformStatusService().get_status()
    assert "warehouse" in status
    assert "cache" in status
    assert "recommendations" in status
    assert "realtime" in status
