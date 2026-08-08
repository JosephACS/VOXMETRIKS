"""Spec 047 recovery — assert 046 artist routers and restored 047 mounts coexist."""

from __future__ import annotations

from app.main import create_app


def _route_paths() -> set[str]:
    app = create_app()
    return {getattr(route, "path", "") for route in app.routes}


def test_046_artist_routers_and_047_mounts_present():
    paths = _route_paths()

    assert any("/artist-space" in p for p in paths), paths
    assert any("/artist-access" in p for p in paths), paths
    assert any(
        "/artist-invitations" in p and p.rstrip("/").endswith("/accept") for p in paths
    ), paths
    assert any("/platform/artist-requests" in p for p in paths), paths

    assert any("/workpanel" in p for p in paths), paths
    assert any("/reports/simple/catalog" in p for p in paths), paths
    assert any("/reports/complex/catalog" in p for p in paths), paths
