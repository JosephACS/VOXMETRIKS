"""
Minimal API tests — health, login, playlists, favorites (API v2 /api/v1).

Run from backend/:
    pytest tests/test_api.py -v
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealth:
    def test_root_returns_metadata(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["app"] == "VOXMETRIK_V2"
        assert data["version"] == "2.0.0"
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"

    def test_health_returns_schema(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("ok", "degraded", "error")
        assert "table_count" in data
        assert "version" in data

    def test_health_ok_with_test_database(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["table_count"] > 0
        assert data.get("database") is None
        assert data.get("tables") == []


class TestLogin:
    def test_login_success(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/users/login",
            json={"login": "demo@voxmetrik.io", "password": "demo123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["username"] == "demo"
        assert data["user"]["email"] == "demo@voxmetrik.io"

    def test_login_invalid_credentials(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/users/login",
            json={"login": "demo", "password": "wrong-password"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_validation_error(self, client: TestClient) -> None:
        response = client.post("/api/v1/users/login", json={"login": "demo"})
        assert response.status_code == 422


class TestPlaylists:
    def test_list_requires_auth(self, client: TestClient) -> None:
        response = client.get("/api/v1/playlists")
        assert response.status_code == 401

    def test_create_list_get_delete_playlist(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        create = client.post(
            "/api/v1/playlists",
            json={"name": "Pytest Playlist", "description": "Minimal test"},
            headers=auth_headers,
        )
        assert create.status_code == 201
        created = create.json()
        assert created["name"] == "Pytest Playlist"
        playlist_id = created["id"]

        listing = client.get("/api/v1/playlists", headers=auth_headers)
        assert listing.status_code == 200
        ids = {p["id"] for p in listing.json()}
        assert playlist_id in ids

        detail = client.get(f"/api/v1/playlists/{playlist_id}", headers=auth_headers)
        assert detail.status_code == 200
        assert detail.json()["name"] == "Pytest Playlist"

        updated = client.put(
            f"/api/v1/playlists/{playlist_id}",
            json={"name": "Pytest Playlist Updated"},
            headers=auth_headers,
        )
        assert updated.status_code == 200
        assert updated.json()["name"] == "Pytest Playlist Updated"

        deleted = client.delete(
            f"/api/v1/playlists/{playlist_id}", headers=auth_headers
        )
        assert deleted.status_code == 200
        assert deleted.json()["deleted"] is True

    def test_add_track_to_playlist(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        create = client.post(
            "/api/v1/playlists",
            json={"name": "Track Test PL"},
            headers=auth_headers,
        )
        assert create.status_code == 201
        playlist_id = create.json()["id"]

        add = client.post(
            f"/api/v1/playlists/{playlist_id}/tracks",
            json={"track_id": 1},
            headers=auth_headers,
        )
        assert add.status_code == 201
        assert add.json()["added"] is True

        detail = client.get(f"/api/v1/playlists/{playlist_id}", headers=auth_headers)
        assert detail.status_code == 200
        track_ids = {t["id_track"] for t in detail.json()["tracks"]}
        assert 1 in track_ids

        remove = client.delete(
            f"/api/v1/playlists/{playlist_id}/tracks/1",
            headers=auth_headers,
        )
        assert remove.status_code == 200
        assert remove.json()["removed"] is True


class TestFavorites:
    def test_list_requires_auth(self, client: TestClient) -> None:
        response = client.get("/api/v1/favorites")
        assert response.status_code == 401

    def test_add_list_remove_favorite(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        track_id = 2
        client.delete(f"/api/v1/favorites/{track_id}", headers=auth_headers)

        add = client.post(f"/api/v1/favorites/{track_id}", headers=auth_headers)
        assert add.status_code == 201
        assert add.json()["favorited"] is True

        listing = client.get("/api/v1/favorites", headers=auth_headers)
        assert listing.status_code == 200
        track_ids = {f["id_track"] for f in listing.json()}
        assert track_id in track_ids

        remove = client.delete(f"/api/v1/favorites/{track_id}", headers=auth_headers)
        assert remove.status_code == 200
        assert remove.json()["removed"] is True

        listing_after = client.get("/api/v1/favorites", headers=auth_headers)
        assert listing_after.status_code == 200
        assert track_id not in {f["id_track"] for f in listing_after.json()}

    def test_favorite_unknown_track_returns_404(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post("/api/v1/favorites/99999", headers=auth_headers)
        assert response.status_code == 404


class TestCatalogSteward:
    """Normal listeners can read catalog but not mutate it (Spotify-like)."""

    def test_demo_cannot_create_artist(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/v1/artists",
            json={"nombre_artista": "Forbidden Artist"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_demo_cannot_create_genre(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/v1/genres",
            json={"nombre_genero": "Forbidden Genre"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_demo_cannot_create_track(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/v1/tracks",
            json={"nombre_track": "Forbidden Track"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_admin_can_create_artist(
        self, client: TestClient, admin_auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/v1/artists",
            json={"nombre_artista": "Steward Artist"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["nombre_artista"] == "Steward Artist"

    def test_demo_can_list_artists(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/v1/artists", headers=auth_headers)
        assert response.status_code == 200
        assert "items" in response.json()


class TestTrackSearch:
    def test_search_by_token(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get(
            "/api/v1/tracks/search",
            params={"q": "golden"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert isinstance(data.get("items"), list)
        assert data.get("total", 0) >= len(data["items"])
        assert len(data["items"]) > 0

    def test_search_accent_insensitive(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get(
            "/api/v1/tracks/search",
            params={"q": "vamonos marte"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert isinstance(data.get("items"), list)
        assert data.get("total", 0) >= len(data["items"])
        assert any("marte" in (t.get("nombre_track") or "").lower() for t in data["items"])
