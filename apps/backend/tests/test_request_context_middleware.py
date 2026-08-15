"""Regression coverage for request correlation under normal and canceled requests."""

from __future__ import annotations

import asyncio

import pytest

from app.core.request_context import RequestContextMiddleware, get_request_id


def _http_scope(request_id: bytes | None = None) -> dict:
    headers = [] if request_id is None else [(b"x-request-id", request_id)]
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/health",
        "raw_path": b"/health",
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 1234),
        "server": ("127.0.0.1", 8000),
    }


def test_request_context_preserves_incoming_id_and_sets_response_header() -> None:
    async def exercise() -> tuple[list[str | None], list[dict]]:
        seen: list[str | None] = []
        sent: list[dict] = []

        async def app(scope, receive, send) -> None:
            seen.append(get_request_id())
            await send({"type": "http.response.start", "status": 204, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        async def receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message: dict) -> None:
            sent.append(message)

        await RequestContextMiddleware(app)(
            _http_scope(b"request-052"), receive, send
        )
        return seen, sent

    seen, sent = asyncio.run(exercise())
    assert seen == ["request-052"]
    headers = dict(sent[0]["headers"])
    assert headers[b"x-request-id"] == b"request-052"
    assert get_request_id() is None


def test_request_context_propagates_cancellation_without_runtime_wrapper() -> None:
    async def exercise() -> None:
        async def canceled_app(scope, receive, send) -> None:
            assert get_request_id()
            raise asyncio.CancelledError

        async def receive() -> dict:
            return {"type": "http.disconnect"}

        async def send(message: dict) -> None:
            raise AssertionError(f"unexpected response: {message}")

        with pytest.raises(asyncio.CancelledError):
            await RequestContextMiddleware(canceled_app)(_http_scope(), receive, send)

    asyncio.run(exercise())
    assert get_request_id() is None
