"""Enterprise V1 API — repository-backed analytics endpoints."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

WAREHOUSE = Path(__file__).resolve().parents[3] / "data" / "warehouse" / "voxmetrik.duckdb"


class TestEnterpriseV1Api:
    def test_dashboard_overview_envelope(self, client: TestClient) -> None:
        response = client.get("/api/v1/dashboard/overview")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert "data" in body
        assert "meta" in body
        data = body["data"]
        assert "total_streams" in data
        assert "top_genres" in data
        assert "growth_trends" in data

    def test_analytics_streams_date_range(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/analytics/streams",
            params={"start_date": "2026-06-01", "end_date": "2026-06-29"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["start_date"] == "2026-06-01"

    def test_top_tracks(self, client: TestClient) -> None:
        response = client.get("/api/v1/tracks/top", params={"limit": 5})
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert isinstance(body["data"], list)

    def test_user_insights_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/users/999999/insights")
        assert response.status_code == 404

    def test_user_insights_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/users/3/insights")
        if response.status_code == 404:
            pytest.skip("user 3 not in test warehouse")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["user_id"] == 3

    def test_track_recommendations(self, client: TestClient) -> None:
        response = client.get("/api/v1/tracks/recommendations/3", params={"limit": 5})
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert isinstance(body["data"], list)
        if body["data"]:
            item = body["data"][0]
            assert "track_id" in item
            assert "score" in item
            assert "reason" in item


@pytest.mark.skipif(not WAREHOUSE.exists(), reason="production warehouse not mounted")
class TestEnterpriseWithProductionWarehouse:
    def test_real_warehouse_top_tracks(self, client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("db_path", str(WAREHOUSE))
        from app.core.config import get_settings
        from app.db.duckdb_client import shutdown_duckdb_client

        get_settings.cache_clear()
        shutdown_duckdb_client()

        response = client.get("/api/v1/tracks/top", params={"limit": 3})
        assert response.status_code == 200
        items = response.json()["data"]
        assert len(items) >= 1
        assert items[0]["popularity"] > 0
