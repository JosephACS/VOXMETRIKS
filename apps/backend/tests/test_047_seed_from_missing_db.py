# -*- coding: utf-8 -*-
"""Spec 047 — integrated demo seed works on a brand-new DB_PATH."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import duckdb

_BACKEND = Path(__file__).resolve().parents[1]


def test_seed_integrated_demo_from_nonexistent_path(tmp_path):
    db_path = tmp_path / "fresh" / "voxmetrik-seed.duckdb"
    assert not db_path.exists()

    env = os.environ.copy()
    env["DB_PATH"] = str(db_path)
    env["db_path"] = str(db_path)
    env["VOXMETRIKS_SEED_DEMO_ACCOUNTS"] = "1"
    env["DEMO_ACCOUNT_PASSWORD"] = "seed-test-secret"
    env["SKIP_SYSTEM_BOOT"] = "1"
    env["RUN_ETL_ON_BOOT"] = "never"
    # Documented default keeps CRM demo seeding enabled.
    env.pop("SEED_DEMO_CRM_USERS", None)

    proc = subprocess.run(
        [sys.executable, "scripts/seed_integrated_demo.py", "--json"],
        cwd=str(_BACKEND),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert db_path.exists()

    report = json.loads(proc.stdout)
    assert report.get("ok") is True
    assert len(report.get("accounts") or []) >= 7

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        users = int(conn.execute("SELECT COUNT(*) FROM app_user").fetchone()[0])
        assert users >= 7
        roles = conn.execute(
            """
            SELECT COUNT(*) FROM app_user_platform_role upr
            JOIN app_platform_role r ON r.id = upr.role_id
            WHERE r.code = 'platform_admin' AND upr.status = 'active'
            """
        ).fetchone()[0]
        assert int(roles) >= 1
    finally:
        conn.close()
