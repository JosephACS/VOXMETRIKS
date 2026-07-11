"""Notification emission API — reusable across platform modules."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.platform.realtime.hub import get_event_hub

from .models import Notification, NotificationKind, NotificationLevel, new_notification
from .store import get_notification_store


class NotificationService:
    def emit(
        self,
        kind: NotificationKind,
        title: str,
        message: str,
        *,
        level: NotificationLevel = NotificationLevel.INFO,
        user_id: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        note = new_notification(
            kind, title, message, level=level, user_id=user_id, meta=meta
        )
        get_notification_store().add(note)
        get_event_hub().publish("notification", note.to_dict(), user_id=user_id)
        return note

    def list_for_user(self, user_id: int, *, limit: int = 30) -> List[Dict[str, Any]]:
        return [n.to_dict() for n in get_notification_store().list_for_user(user_id, limit=limit)]

    def favorite_added(self, user_id: int, track_title: str) -> Notification:
        return self.emit(
            NotificationKind.FAVORITE_ADDED,
            "Agregado a favoritos",
            track_title,
            level=NotificationLevel.SUCCESS,
            user_id=user_id,
        )

    def pipeline_completed(self, status: str, *, rows: int = 0) -> Notification:
        return self.emit(
            NotificationKind.PIPELINE_RUN,
            "Pipeline ejecutado",
            f"Estado: {status}" + (f" ({rows} filas)" if rows else ""),
            level=NotificationLevel.INFO if status == "success" else NotificationLevel.WARNING,
        )

    def recommendations_refreshed(self, user_id: Optional[int] = None) -> Notification:
        return self.emit(
            NotificationKind.RECOMMENDATIONS_REFRESHED,
            "Recomendaciones actualizadas",
            "Tu feed personalizado fue refrescado.",
            level=NotificationLevel.INFO,
            user_id=user_id,
        )

    def recoverable_error(self, message: str, *, user_id: Optional[int] = None) -> Notification:
        return self.emit(
            NotificationKind.RECOVERABLE_ERROR,
            "Algo salió mal",
            message,
            level=NotificationLevel.WARNING,
            user_id=user_id,
        )


_svc = NotificationService()


def get_notification_service() -> NotificationService:
    return _svc
