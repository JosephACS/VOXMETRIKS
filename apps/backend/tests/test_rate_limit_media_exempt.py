from __future__ import annotations

from fastapi import Request

from app.core.rate_limit import (
    check_global_rate_limit,
    clear_rate_limit_buckets,
    is_rate_limit_exempt,
)


def test_cover_and_audio_paths_are_exempt():
    assert is_rate_limit_exempt("/api/v1/tracks/42/cover")
    assert is_rate_limit_exempt("/api/v1/artists/7/cover")
    assert is_rate_limit_exempt("/api/v1/tracks/42/audio-source")
    assert is_rate_limit_exempt("/health")
    assert not is_rate_limit_exempt("/api/v1/tracks")
    assert not is_rate_limit_exempt("/api/v1/smart/home")


def test_exempt_paths_do_not_consume_global_budget():
    clear_rate_limit_buckets()
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/api/v1/tracks/1/cover",
        "raw_path": b"/api/v1/tracks/1/cover",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("127.0.0.1", 8000),
    }
    request = Request(scope)
    for _ in range(50):
        check_global_rate_limit(request, max_calls=5, window_sec=60)
