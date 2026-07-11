"""I3 auth smoke via FastAPI TestClient (conftest test DB pattern)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Admin\Documents\Tarea\Proyectos\Ariosto\voxmetriks")
BACKEND = ROOT / "apps" / "backend"
OUT = ROOT / "automation" / "specs" / "016-identity-and-organizations" / "evidence" / "_i3_auth_smoke.txt"

sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

lines: list[str] = []


def log(msg: str = "") -> None:
    print(msg)
    lines.append(msg)


def main() -> int:
    os.environ.setdefault("AUTH_RATE_LIMIT", "0")
    os.environ.setdefault("GLOBAL_RATE_LIMIT", "0")
    os.environ.setdefault("LOG_TO_FILES", "false")
    os.environ["RUN_ETL_ON_BOOT"] = "never"
    os.environ["SKIP_SYSTEM_BOOT"] = "1"

    from fastapi.testclient import TestClient

    import tests.conftest as cf

    os.environ["db_path"] = str(cf._TEST_DB_PATH)
    from app.core.config import get_settings
    from app.core.database import close_read_pool
    from app.db.duckdb_client import shutdown_duckdb_client

    get_settings.cache_clear()
    shutdown_duckdb_client()
    close_read_pool()
    cf._init_test_database(cf._TEST_DB_PATH)

    from app.main import app

    exit_code = 0
    try:
        with TestClient(app) as client:
            r = client.get("/health")
            log(f"GET /health -> {r.status_code} body={r.text[:500]}")
            if r.status_code != 200:
                exit_code = 1

            r = client.post(
                "/api/v1/users/login",
                json={"login": "demo", "password": "demo123", "remember": True},
            )
            body = r.text[:800]
            log(f"POST /api/v1/users/login -> {r.status_code} body={body}")
            if r.status_code != 200:
                exit_code = 1
                token = None
            else:
                data = r.json()
                token = data.get("token")
                log(f"token_present={bool(token)} keys={list(data.keys())}")

            if token:
                r = client.get(
                    "/api/v1/users/me",
                    headers={"Authorization": f"Bearer {token}"},
                )
                log(f"GET /api/v1/users/me -> {r.status_code} body={r.text[:800]}")
                if r.status_code != 200:
                    exit_code = 1

                r = client.post(
                    "/api/v1/users/logout",
                    headers={"Authorization": f"Bearer {token}"},
                )
                log(f"POST /api/v1/users/logout -> {r.status_code} body={r.text[:400]}")
                if r.status_code != 200:
                    exit_code = 1

                r = client.get(
                    "/api/v1/users/me",
                    headers={"Authorization": f"Bearer {token}"},
                )
                log(f"GET /api/v1/users/me (after logout) -> {r.status_code} body={r.text[:400]}")
                if r.status_code == 401:
                    log("PASS: bearer rejected after logout")
                else:
                    log("FAIL: expected 401 after logout")
                    exit_code = 1
            else:
                log("FAIL: no token from login")
                exit_code = 1
    except Exception as exc:
        import traceback

        log(f"FAIL exception: {type(exc).__name__}: {exc}")
        log(traceback.format_exc())
        exit_code = 1
    finally:
        shutdown_duckdb_client()
        close_read_pool()

    OUT.write_text("\n".join(lines) + f"\nEXIT={exit_code}\n", encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
