"""Smoke test for a running Voxmetriks API.

Run after starting the backend:
    python scripts/smoke_api.py --base-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class Account:
    login: str
    password: str


def _assert_status(response: httpx.Response, expected: int, label: str) -> None:
    if response.status_code != expected:
        raise AssertionError(
            f"{label}: expected HTTP {expected}, got {response.status_code}: "
            f"{response.text[:300]}"
        )


def _login(client: httpx.Client, account: Account) -> tuple[dict[str, str], dict[str, Any]]:
    response = client.post(
        "/api/v1/users/login",
        json={"login": account.login, "password": account.password, "remember": True},
    )
    _assert_status(response, 200, f"login {account.login}")
    payload = response.json()
    token = payload.get("token")
    if not token:
        raise AssertionError(f"login {account.login}: missing token")
    return {"Authorization": f"Bearer {token}"}, payload


def run_smoke(base_url: str, demo: Account, admin: Account) -> None:
    with httpx.Client(base_url=base_url.rstrip("/"), timeout=10.0) as client:
        health = client.get("/health")
        _assert_status(health, 200, "health")
        health_payload = health.json()
        if health_payload.get("status") not in {"ok", "degraded"}:
            raise AssertionError(f"health: unexpected status {health_payload!r}")
        if health_payload.get("database") or health_payload.get("tables"):
            raise AssertionError("health: public response exposed database details")
        print(f"[ok] health {health_payload.get('status')} ({health_payload.get('table_count', 0)} tables)")

        demo_headers, demo_payload = _login(client, demo)
        if demo_payload["user"].get("role") != "user":
            raise AssertionError(f"demo role mismatch: {demo_payload['user']!r}")
        print("[ok] demo login role=user")

        admin_headers, admin_payload = _login(client, admin)
        if admin_payload["user"].get("role") not in {"engineer", "admin"}:
            raise AssertionError(f"admin role mismatch: {admin_payload['user']!r}")
        print(f"[ok] admin login role={admin_payload['user'].get('role')}")

        demo_explorer = client.get("/api/v1/analytics/explorer/tables", headers=demo_headers)
        _assert_status(demo_explorer, 403, "demo explorer denied")
        print("[ok] demo denied from explorer")

        admin_explorer = client.get("/api/v1/analytics/explorer/tables", headers=admin_headers)
        _assert_status(admin_explorer, 200, "admin explorer allowed")
        table_names = {item["name"] for item in admin_explorer.json()}
        if {"app_user", "app_session"} & table_names:
            raise AssertionError("explorer: sensitive tables are visible")
        print("[ok] admin explorer allowed and sensitive tables hidden")

        preview = client.get(
            "/api/v1/analytics/explorer/preview/dim_track",
            headers=admin_headers,
            params={"limit": 3},
        )
        _assert_status(preview, 200, "admin dim_track preview")
        if "password_hash" in preview.json().get("columns", []):
            raise AssertionError("preview: sensitive column exposed")
        print("[ok] preview does not expose sensitive columns")

        logout = client.post("/api/v1/users/logout", headers=demo_headers)
        _assert_status(logout, 200, "demo logout")
        expired_me = client.get("/api/v1/users/me", headers=demo_headers)
        _assert_status(expired_me, 401, "demo token after logout")
        print("[ok] logout invalidates server session")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Voxmetriks API smoke test.")
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
    except Exception as exc:
        print(f"[fail] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
