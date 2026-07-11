"""Production infrastructure — error envelope, cache, logging, security headers."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestErrorEnvelope:
    def test_validation_error_envelope(self, client: TestClient) -> None:
        response = client.get("/api/v1/users/not-an-int/insights")
        assert response.status_code == 422
        body = response.json()
        assert body["status"] == "error"
        assert "message" in body
        assert "details" in body

    def test_not_found_envelope(self, client: TestClient) -> None:
        response = client.get("/api/v1/users/999999/insights")
        assert response.status_code == 404
        body = response.json()
        assert body["status"] == "error"
        assert body["message"]

    def test_unknown_route_envelope(self, client: TestClient) -> None:
        response = client.get("/api/v1/does-not-exist")
        assert response.status_code == 404
        body = response.json()
        assert body["status"] == "error"


class TestSecurityHeaders:
    def test_security_headers_present(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert "X-Request-ID" in response.headers
        assert "X-Response-Time-Ms" in response.headers


class TestCacheConfig:
    def test_dashboard_cache_hit(self, client: TestClient) -> None:
        first = client.get("/api/v1/dashboard/overview")
        second = client.get("/api/v1/dashboard/overview")
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json() == second.json()


class TestPagination:
    def test_top_tracks_pagination_optional(self, client: TestClient) -> None:
        legacy = client.get("/api/v1/tracks/top", params={"limit": 5})
        assert legacy.status_code == 200
        assert legacy.json()["meta"].get("limit") == 5

        paged = client.get("/api/v1/tracks/top", params={"page": 1, "page_size": 5})
        assert paged.status_code == 200
        meta = paged.json()["meta"]
        assert meta.get("page") == 1
        assert meta.get("page_size") == 5
