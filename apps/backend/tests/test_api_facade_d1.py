"""Spec 014 D1 — API facade auth, ownership, and collision winners."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestPublicIntentional:
    def test_health_public(self, client: TestClient) -> None:
        assert client.get("/health").status_code == 200

    def test_auth_config_public(self, client: TestClient) -> None:
        assert client.get("/api/v1/users/auth-config").status_code == 200

    def test_login_public(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/users/login",
            json={"login": "demo", "password": "demo123", "remember": True},
        )
        assert resp.status_code == 200

    def test_catalog_tracks_list_public(self, client: TestClient) -> None:
        assert client.get("/api/v1/tracks", params={"limit": 1}).status_code == 200


class TestAuthRequired401:
    def test_dashboard_overview_requires_auth(self, client: TestClient) -> None:
        assert client.get("/api/v1/dashboard/overview").status_code == 401

    def test_analytics_streams_requires_auth(self, client: TestClient) -> None:
        assert client.get("/api/v1/analytics/streams").status_code == 401

    def test_tracks_top_requires_auth(self, client: TestClient) -> None:
        assert client.get("/api/v1/tracks/top").status_code == 401

    def test_user_insights_requires_auth(self, client: TestClient) -> None:
        assert client.get("/api/v1/users/1/insights").status_code == 401

    def test_v2_dashboard_requires_auth(self, client: TestClient) -> None:
        assert client.get("/api/v2/dashboard/overview").status_code == 401

    def test_ai_natural_search_requires_auth(self, client: TestClient) -> None:
        assert (
            client.post("/api/v1/ai/search/natural", json={"query": "upbeat pop"}).status_code
            == 401
        )

    def test_stats_summary_requires_auth(self, client: TestClient) -> None:
        assert client.get("/api/v1/stats/summary").status_code == 401

    def test_analytics_engagement_requires_auth(self, client: TestClient) -> None:
        assert client.get("/api/v1/analytics/engagement").status_code == 401


class TestRoleAndOwnership:
    def test_demo_cannot_read_other_user_insights(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        me = client.get("/api/v1/users/me", headers=auth_headers)
        assert me.status_code == 200
        my_id = me.json()["id"]
        other = my_id + 99999
        resp = client.get(f"/api/v1/users/{other}/insights", headers=auth_headers)
        assert resp.status_code == 403

    def test_demo_can_read_own_insights_or_404(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        me = client.get("/api/v1/users/me", headers=auth_headers)
        my_id = me.json()["id"]
        resp = client.get(f"/api/v1/users/{my_id}/insights", headers=auth_headers)
        assert resp.status_code in (200, 404)

    def test_demo_forbidden_synthetic_limits(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        assert client.get("/api/v1/stats/synthetic/limits", headers=auth_headers).status_code == 403

    def test_admin_can_synthetic_limits(
        self, client: TestClient, admin_auth_headers: dict[str, str]
    ) -> None:
        assert (
            client.get("/api/v1/stats/synthetic/limits", headers=admin_auth_headers).status_code
            == 200
        )


class TestCanonicalContractsWithAuth:
    def test_dashboard_overview_envelope(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/v1/dashboard/overview", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert "total_streams" in body["data"]

    def test_analytics_streams_envelope(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get(
            "/api/v1/analytics/streams",
            params={"start_date": "2026-06-01", "end_date": "2026-06-29"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_tracks_top_envelope(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/v1/tracks/top", params={"limit": 5}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert isinstance(response.json()["data"], list)

    def test_v2_dashboard_compat(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/v2/dashboard/overview", headers=auth_headers)
        assert response.status_code == 200
        assert "total_streams" in response.json()

    def test_collision_winner_is_enterprise_envelope(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """GET /api/v1/dashboard/overview must keep enterprise {status,data,meta} shape."""
        body = client.get("/api/v1/dashboard/overview", headers=auth_headers).json()
        assert set(body.keys()) >= {"status", "data"}
        assert body["status"] == "success"
