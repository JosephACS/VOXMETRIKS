"""In-memory notification store with bounded history."""

from __future__ import annotations

import threading
from collections import deque
from typing import Deque, Iterable, List, Optional

from .models import Notification

_MAX_GLOBAL = 500
_MAX_PER_USER = 100


class NotificationStore:
    def __init__(self) -> None:
        self._global: Deque[Notification] = deque(maxlen=_MAX_GLOBAL)
        self._by_user: dict[int, Deque[Notification]] = {}
        self._lock = threading.RLock()

    def add(self, notification: Notification) -> Notification:
        with self._lock:
            self._global.appendleft(notification)
            if notification.user_id is not None:
                uid = notification.user_id
                if uid not in self._by_user:
                    self._by_user[uid] = deque(maxlen=_MAX_PER_USER)
                self._by_user[uid].appendleft(notification)
        return notification

    def list_for_user(self, user_id: int, *, limit: int = 30) -> List[Notification]:
        with self._lock:
            items = list(self._by_user.get(user_id, []))
        return items[:limit]

    def list_global(self, *, limit: int = 30) -> List[Notification]:
        with self._lock:
            return list(self._global)[:limit]

    def count(self) -> int:
        with self._lock:
            return len(self._global)

    def since(self, user_id: Optional[int], after_id: Optional[str]) -> Iterable[Notification]:
        items = self.list_for_user(user_id, limit=50) if user_id else self.list_global(limit=50)
        if not after_id:
            return items
        found = False
        out: List[Notification] = []
        for n in items:
            if found:
                out.append(n)
            elif n.id == after_id:
                found = True
        return out


_store = NotificationStore()


def get_notification_store() -> NotificationStore:
    return _store
