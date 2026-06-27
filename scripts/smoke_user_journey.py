"""End-to-end user journey smoke test against a running Voxmetriks API.

Run after starting the backend:
    python scripts/smoke_user_journey.py --base-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Any

import httpx

from smoke_api import Account, _assert_status, _login, run_smoke


def _pick_track_id(client: httpx.Client, headers: dict[str, str]) -> int:
    response = client.get("/api/v1/tracks/search", headers=headers, params={"q": "love", "limit": 1})
    _assert_status(response, 200, "search tracks")
    items = response.json()
    if not isinstance(items, list) or not items:
        fallback = client.get("/api/v1/tracks", headers=headers, params={"limit": 1})
        _assert_status(fallback, 200, "list tracks fallback")
        page = fallback.json()
        items = page.get("items") or []
    if not items:
        raise AssertionError("journey: no tracks available")
    track_id = items[0].get("id_track")
    if not track_id:
        raise AssertionError("journey: track missing id_track")
    return int(track_id)


def run_user_journey(base_url: str, demo: Account) -> None:
    with httpx.Client(base_url=base_url.rstrip("/"), timeout=15.0) as client:
        headers, _ = _login(client, demo)

        track_id = _pick_track_id(client, headers)
        print(f"[ok] picked track {track_id}")

        search = client.get("/api/v1/tracks/search", headers=headers, params={"q": "love", "limit": 3})
        _assert_status(search, 200, "search")
        print("[ok] search tracks")

        fav_add = client.post(f"/api/v1/favorites/{track_id}", headers=headers)
        _assert_status(fav_add, 201, "add favorite")
        fav_list = client.get("/api/v1/favorites", headers=headers)
        _assert_status(fav_list, 200, "list favorites")
        fav_ids = {item.get("id_track") for item in fav_list.json()}
        if track_id not in fav_ids:
            raise AssertionError("journey: favorite not listed")
        print("[ok] favorite add/list")

        playlist = client.post(
            "/api/v1/playlists",
            headers=headers,
            json={"name": "Smoke Journey", "description": "Automated smoke playlist"},
        )
        _assert_status(playlist, 201, "create playlist")
        pl_id = playlist.json().get("id")
        if not pl_id:
            raise AssertionError("journey: playlist missing id")
        add_track = client.post(
            f"/api/v1/playlists/{pl_id}/tracks",
            headers=headers,
            json={"track_id": track_id},
        )
        _assert_status(add_track, 201, "add track to playlist")
        pl_detail = client.get(f"/api/v1/playlists/{pl_id}", headers=headers)
        _assert_status(pl_detail, 200, "get playlist detail")
        print(f"[ok] playlist {pl_id} with track")

        recs = client.get("/api/v1/analytics/recommendations", headers=headers, params={"limit": 3})
        _assert_status(recs, 200, "recommendations")
        if not recs.json().get("for_you"):
            raise AssertionError("journey: recommendations empty")
        print("[ok] recommendations")

        history = client.get("/api/v1/analytics/history", headers=headers, params={"limit": 3})
        _assert_status(history, 200, "history hub")
        print("[ok] history hub")

        client.delete(f"/api/v1/favorites/{track_id}", headers=headers)
        client.delete(f"/api/v1/playlists/{pl_id}", headers=headers)
        logout = client.post("/api/v1/users/logout", headers=headers)
        _assert_status(logout, 200, "logout")
        print("[ok] cleanup favorite/playlist and logout")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Voxmetriks security + user journey smoke tests.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--demo-login", default="demo")
    parser.add_argument("--demo-password", default="demo123")
    parser.add_argument("--admin-login", default="admin")
    parser.add_argument("--admin-password", default="admin123")
    args = parser.parse_args()

    try:
        run_smoke(
            args.base_url,
            Account(args.demo_login, args.demo_password),
            Account(args.admin_login, args.admin_password),
        )
        run_user_journey(args.base_url, Account(args.demo_login, args.demo_password))
    except Exception as exc:
        print(f"[fail] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
