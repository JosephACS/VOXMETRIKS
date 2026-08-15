"""Request context middleware — correlation ID and authenticated user logging."""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Any

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return request_id_ctx.get()


class RequestContextMiddleware:
    """Pure ASGI correlation context that remains safe on client disconnects.

    ``BaseHTTPMiddleware.call_next`` turns a canceled downstream response into
    ``RuntimeError('No response returned.')``. Navigating between SPA routes
    legitimately cancels obsolete requests, so request correlation must not
    reclassify those disconnects as application failures.
    """

    def __init__(self, app: ASGIApp, **_: Any) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = Headers(scope=scope).get("X-Request-ID")
        req_id = incoming.strip() if incoming and incoming.strip() else uuid.uuid4().hex
        token = request_id_ctx.set(req_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)["X-Request-ID"] = req_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            request_id_ctx.reset(token)
