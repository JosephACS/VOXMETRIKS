"""V2 architecture scaffold tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.duckdb_client import shutdown_duckdb_client
from app.main import app


def test_health_ok():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"healthy", "degraded", "unhealthy", "ok", "error"}
    shutdown_duckdb_client()


def test_v2_module_status_endpoints():
    client = TestClient(app)
    for path in (
        "/api/v2/users/status",
        "/api/v2/stream/status",
        "/api/v2/analytics/status",
        "/api/v2/search/status",
        "/api/v2/recommendations/status",
    ):
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.json()["status"] == "success"
    shutdown_duckdb_client()
