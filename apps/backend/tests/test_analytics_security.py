"""Security tests — explorer and warehouse engineer-only access."""

from __future__ import annotations

from fastapi.testclient import TestClient

EXPLORER_TABLES = "/api/v1/analytics/explorer/tables"
EXPLORER_PREVIEW = "/api/v1/analytics/explorer/preview/dim_track"
WAREHOUSE = "/api/v1/analytics/warehouse"


class TestAnalyticsExplorerSecurity:
    def test_anonymous_cannot_list_explorer_tables(self, client: TestClient) -> None:
        response = client.get(EXPLORER_TABLES)
        assert response.status_code == 401

    def test_anonymous_cannot_preview_table(self, client: TestClient) -> None:
        response = client.get(EXPLORER_PREVIEW)
        assert response.status_code == 401

    def test_anonymous_cannot_access_warehouse(self, client: TestClient) -> None:
        response = client.get(WAREHOUSE)
        assert response.status_code == 401

    def test_demo_cannot_list_explorer_tables(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get(EXPLORER_TABLES, headers=auth_headers)
        assert response.status_code == 403

    def test_demo_cannot_preview_table(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get(EXPLORER_PREVIEW, headers=auth_headers)
        assert response.status_code == 403

    def test_demo_cannot_access_warehouse(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get(WAREHOUSE, headers=auth_headers)
        assert response.status_code == 403

    def test_admin_can_list_explorer_tables(
        self, client: TestClient, admin_auth_headers: dict[str, str]
    ) -> None:
        response = client.get(EXPLORER_TABLES, headers=admin_auth_headers)
        assert response.status_code == 200
        names = {t["name"] for t in response.json()}
        assert "dim_track" in names
        assert "app_user" not in names
        assert "app_session" not in names

    def test_admin_can_preview_dim_track(
        self, client: TestClient, admin_auth_headers: dict[str, str]
    ) -> None:
        response = client.get(EXPLORER_PREVIEW, headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "dim_track"
        assert "password_hash" not in data.get("columns", [])

    def test_admin_cannot_preview_app_user(
        self, client: TestClient, admin_auth_headers: dict[str, str]
    ) -> None:
        response = client.get(
            "/api/v1/analytics/explorer/preview/app_user",
            headers=admin_auth_headers,
        )
        assert response.status_code == 403

    def test_admin_can_access_warehouse(
        self, client: TestClient, admin_auth_headers: dict[str, str]
    ) -> None:
        response = client.get(WAREHOUSE, headers=admin_auth_headers)
        assert response.status_code == 200
        assert "pipeline_status" in response.json()


class TestStatsWriteSecurity:
    def test_anonymous_cannot_import(self, client: TestClient) -> None:
        response = client.post("/api/v1/stats/import", json={})
        assert response.status_code == 401

    def test_demo_cannot_import(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post("/api/v1/stats/import", json={}, headers=auth_headers)
        assert response.status_code == 403

    def test_anonymous_cannot_synthetic(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/stats/synthetic",
            json={"multiplier": 2},
        )
        assert response.status_code == 401

    def test_demo_cannot_synthetic(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/v1/stats/synthetic",
            json={"multiplier": 2},
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestRoleBasedAccessControl:
    def test_demo_login_returns_user_role(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/users/login",
            json={"login": "demo", "password": "demo123", "remember": True},
        )
        assert response.status_code == 200
        assert response.json()["user"]["role"] == "user"

    def test_admin_login_returns_admin_role(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/users/login",
            json={"login": "admin", "password": "admin123", "remember": True},
        )
        assert response.status_code == 200
        assert response.json()["user"]["role"] == "admin"

    def test_engineer_login_returns_engineer_role(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/users/login",
            json={"login": "engineer", "password": "engineer123", "remember": True},
        )
        assert response.status_code == 200
        assert response.json()["user"]["role"] == "engineer"

    def test_engineer_cannot_mutate_catalog(self, client: TestClient) -> None:
        login = client.post(
            "/api/v1/users/login",
            json={"login": "engineer", "password": "engineer123", "remember": True},
        )
        token = login.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            "/api/v1/catalog/artists",
            json={"nombre_artista": "Engineer Should Fail"},
            headers=headers,
        )
        assert resp.status_code == 403
