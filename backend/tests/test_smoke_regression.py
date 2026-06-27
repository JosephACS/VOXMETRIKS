"""Critical user-facing smoke regression flow."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _login(client: TestClient, login: str, password: str) -> tuple[dict[str, str], dict]:
    response = client.post(
        "/api/v1/users/login",
        json={"login": login, "password": password, "remember": True},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["token"]
    return {"Authorization": f"Bearer {payload['token']}"}, payload


class TestCriticalSmokeRegression:
    def test_health_auth_rbac_preview_and_logout(self, client: TestClient) -> None:
        health = client.get("/health")
        assert health.status_code == 200
        health_payload = health.json()
        assert health_payload["status"] == "ok"
        assert health_payload["table_count"] > 0
        assert health_payload.get("database") is None
        assert health_payload.get("tables") == []

        demo_headers, demo_payload = _login(client, "demo", "demo123")
        assert demo_payload["user"]["role"] == "user"

        admin_headers, admin_payload = _login(client, "admin", "admin123")
        assert admin_payload["user"]["role"] == "engineer"

        demo_explorer = client.get(
            "/api/v1/analytics/explorer/tables",
            headers=demo_headers,
        )
        assert demo_explorer.status_code == 403

        admin_explorer = client.get(
            "/api/v1/analytics/explorer/tables",
            headers=admin_headers,
        )
        assert admin_explorer.status_code == 200
        table_names = {item["name"] for item in admin_explorer.json()}
        assert "dim_track" in table_names
        assert "app_user" not in table_names
        assert "app_session" not in table_names

        preview = client.get(
            "/api/v1/analytics/explorer/preview/dim_track",
            headers=admin_headers,
            params={"limit": 3},
        )
        assert preview.status_code == 200
        assert "password_hash" not in preview.json().get("columns", [])

        logout = client.post("/api/v1/users/logout", headers=demo_headers)
        assert logout.status_code == 200
        assert logout.json()["ok"] is True

        expired_session = client.get("/api/v1/users/me", headers=demo_headers)
        assert expired_session.status_code == 401
