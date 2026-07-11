"""Lightweight in-process event hub for SSE broadcasts."""

from __future__ import annotations

import asyncio
import json
import threading
from collections import defaultdict
from typing import Any, AsyncIterator, Dict, List, Optional, Set


class EventHub:
    """Fan-out events to SSE subscribers (single-process)."""

    def __init__(self) -> None:
        self._queues: dict[int, asyncio.Queue] = {}
        self._global_queues: Set[asyncio.Queue] = set()
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def subscribe(self, user_id: Optional[int] = None) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=64)
        with self._lock:
            if user_id is None:
                self._global_queues.add(q)
            else:
                self._queues[user_id] = q
        return q

    def unsubscribe(self, q: asyncio.Queue, user_id: Optional[int] = None) -> None:
        with self._lock:
            if user_id is None:
                self._global_queues.discard(q)
            else:
                if self._queues.get(user_id) is q:
                    del self._queues[user_id]

    def publish(self, event: str, data: Dict[str, Any], *, user_id: Optional[int] = None) -> None:
        payload = {"event": event, "data": data}
        targets: List[asyncio.Queue] = []
        with self._lock:
            targets.extend(self._global_queues)
            if user_id is not None and user_id in self._queues:
                targets.append(self._queues[user_id])

        for q in targets:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                pass

    async def stream(self, user_id: Optional[int] = None) -> AsyncIterator[str]:
        q = self.subscribe(user_id)
        try:
            yield f"event: connected\ndata: {json.dumps({'ok': True})}\n\n"
            while True:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=25.0)
                    yield f"event: {msg['event']}\ndata: {json.dumps(msg['data'])}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            self.unsubscribe(q, user_id)


_hub = EventHub()


def get_event_hub() -> EventHub:
    return _hub
