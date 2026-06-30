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
        assert admin_payload["user"]["role"] == "admin"

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

    def test_home_bff_returns_rails(self, client: TestClient) -> None:
        headers, _ = _login(client, "demo", "demo123")
        response = client.get("/api/v1/dashboard/home", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        assert "summary" in payload
        assert "top_tracks" in payload
        assert "discover" in payload
        assert "genres" in payload
        assert isinstance(payload["top_tracks"], list)

    def test_search_tracks_paginated(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/tracks/search",
            params={"q": "de", "page": 1, "limit": 5},
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert "items" in payload
        assert "total" in payload
        assert len(payload["items"]) <= 5

    def test_tracks_cursor_pagination(self, client: TestClient) -> None:
        first = client.get(
            "/api/v1/tracks",
            params={"limit": 2, "use_cursor": True, "include_total": True},
        )
        assert first.status_code == 200, first.text
        body = first.json()
        assert body.get("items")
        assert body.get("has_more") is True
        cursor = body.get("next_cursor")
        assert cursor

        second = client.get(
            "/api/v1/tracks",
            params={"limit": 2, "use_cursor": True, "cursor": cursor},
        )
        assert second.status_code == 200, second.text
        next_items = second.json().get("items") or []
        first_ids = {t["id_track"] for t in body["items"]}
        second_ids = {t["id_track"] for t in next_items}
        assert first_ids.isdisjoint(second_ids)
