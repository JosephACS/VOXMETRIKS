"""In-app notification models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4


class NotificationLevel(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class NotificationKind(str, Enum):
    FAVORITE_ADDED = "favorite_added"
    QUEUE_UPDATED = "queue_updated"
    PLAYLIST_CREATED = "playlist_created"
    AUDIO_UNAVAILABLE = "audio_unavailable"
    RECOMMENDATIONS_REFRESHED = "recommendations_refreshed"
    PIPELINE_RUN = "pipeline_run"
    RECOVERABLE_ERROR = "recoverable_error"
    SYSTEM = "system"


@dataclass
class Notification:
    id: str
    kind: NotificationKind
    level: NotificationLevel
    title: str
    message: str
    user_id: Optional[int] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "meta": self.meta,
        }


def new_notification(
    kind: NotificationKind,
    title: str,
    message: str,
    *,
    level: NotificationLevel = NotificationLevel.INFO,
    user_id: Optional[int] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Notification:
    return Notification(
        id=str(uuid4()),
        kind=kind,
        level=level,
        title=title,
        message=message,
        user_id=user_id,
        meta=meta or {},
    )
