"""I6 auth smoke against pytest DuckDB (not production warehouse)."""
from __future__ import annotations

import os
from pathlib import Path

from app.core.config import get_settings
from app.core.database import close_read_pool
from app.db.duckdb_client import shutdown_duckdb_client
from app.main import app
from fastapi.testclient import TestClient

get_settings.cache_clear()
shutdown_duckdb_client()
close_read_pool()

lines: list[str] = []
with TestClient(app) as c:
    h = c.get("/api/v1/health")
    lines.append(f"health={h.status_code}")
    login = c.post(
        "/api/v1/users/login",
        json={"login": "demo", "password": "demo123", "remember": True},
    )
    lines.append(f"login={login.status_code}")
    token = login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    me = c.get("/api/v1/users/me", headers=headers)
    lines.append(f"me={me.status_code}")
    cur = c.get("/api/v1/organizations/current", headers=headers)
    lines.append(
        f"orgs_current={cur.status_code} context={cur.json().get('context')}"
    )
    listed = c.get("/api/v1/organizations", headers=headers)
    n = len(listed.json()) if listed.status_code == 200 else None
    lines.append(f"orgs_list={listed.status_code} n={n}")
    logout = c.post("/api/v1/users/logout", headers=headers)
    lines.append(f"logout={logout.status_code}")
    me2 = c.get("/api/v1/users/me", headers=headers)
    lines.append(f"me_after_logout={me2.status_code}")

out = Path(__file__).with_name("_i6_auth_smoke.txt")
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
