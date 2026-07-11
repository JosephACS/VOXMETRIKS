"""Spec 014 D2 — package-by-domain shims and canonical imports."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestCompatibilityImports:
    def test_identity_auth_deps_canonical(self) -> None:
        from app.packages.identity.services.auth_deps import require_user_id

        assert callable(require_user_id)

    def test_users_shim_reexports_identity(self) -> None:
        from app.packages.identity.services import auth_deps as identity_auth
        from app.packages.users.services import auth_deps as users_auth

        assert users_auth.require_user_id is identity_auth.require_user_id
        assert users_auth.ensure_self_or_admin is identity_auth.ensure_self_or_admin

    def test_catalog_and_streaming_shim(self) -> None:
        from app.packages.catalog.services import track_service as catalog_tracks
        from app.packages.streaming.services import track_service as streaming_tracks

        assert streaming_tracks.get_tracks is catalog_tracks.get_tracks

    def test_engagement_and_streaming_shim(self) -> None:
        from app.packages.engagement.services import playlist_service as eng
        from app.packages.streaming.services import playlist_service as stream

        assert stream.list_playlists is eng.list_playlists

    def test_routers_mountable(self) -> None:
        from app.packages.catalog.routes import artists_router, genres_router, tracks_router
        from app.packages.engagement.routes import (
            dashboard_router,
            favorites_router,
            playlists_router,
        )
        from app.packages.identity.routes import users_router

        for r in (
            artists_router,
            genres_router,
            tracks_router,
            playlists_router,
            favorites_router,
            dashboard_router,
            users_router,
        ):
            assert r.prefix.startswith("/")


class TestDomainSmokePreservesD1:
    def test_login_and_catalog(self, client: TestClient) -> None:
        login = client.post(
            "/api/v1/users/login",
            json={"login": "demo", "password": "demo123", "remember": True},
        )
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['token']}"}

        tracks = client.get("/api/v1/tracks", params={"limit": 1})
        assert tracks.status_code == 200

        playlists = client.get("/api/v1/playlists", headers=headers)
        assert playlists.status_code == 200

        favorites = client.get("/api/v1/favorites", headers=headers)
        assert favorites.status_code == 200

        overview = client.get("/api/v1/dashboard/overview", headers=headers)
        assert overview.status_code == 200

        anon = client.get("/api/v1/dashboard/overview")
        assert anon.status_code == 401
