# -*- coding: utf-8 -*-
"""Create or update the first platform admin from environment variables.

Production-safe bootstrap — no demo users, no default passwords.

Required env:
  BOOTSTRAP_ADMIN_EMAIL
  BOOTSTRAP_ADMIN_PASSWORD   (must pass password policy)

Optional:
  BOOTSTRAP_ADMIN_USERNAME   (default: admin)
  DB_PATH                    (warehouse path)

Usage (from apps/backend):
  set BOOTSTRAP_ADMIN_EMAIL=ops@example.com
  set BOOTSTRAP_ADMIN_PASSWORD=...
  python scripts/bootstrap_admin.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

os.chdir(_BACKEND)


def main() -> int:
    from dotenv import load_dotenv

    load_dotenv(_BACKEND / ".env")
    load_dotenv(_BACKEND.parent.parent / ".env", override=False)

    email = (os.environ.get("BOOTSTRAP_ADMIN_EMAIL") or "").strip().lower()
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD") or ""
    username = (os.environ.get("BOOTSTRAP_ADMIN_USERNAME") or "admin").strip()

    if not email or "@" not in email:
        print("ERROR: BOOTSTRAP_ADMIN_EMAIL is required", file=sys.stderr)
        return 1
    if not password:
        print("ERROR: BOOTSTRAP_ADMIN_PASSWORD is required", file=sys.stderr)
        return 1

    from app.core.config import get_settings
    from app.core.database import using_write_conn
    from app.core.time_util import utc_now
    from app.packages.identity.services.password_security import (
        PasswordPolicyError,
        hash_password,
        validate_account_password,
    )
    from app.packages.identity.services.user_storage import ensure_user_tables

    try:
        validate_account_password(password)
    except PasswordPolicyError as exc:
        print(f"ERROR: password policy: {exc}", file=sys.stderr)
        return 1

    settings = get_settings()
    print(f"Using warehouse: {settings.db_path_resolved}")
    pwd_hash = hash_password(password)

    with using_write_conn() as conn:
        ensure_user_tables(conn)
        row = conn.execute(
            """
            SELECT id FROM app_user
            WHERE LOWER(email) = ? OR LOWER(username) = ?
            ORDER BY CASE WHEN LOWER(email) = ? THEN 0 ELSE 1 END
            LIMIT 1
            """,
            [email, username.lower(), email],
        ).fetchone()

        if row:
            # DuckDB unique ART indexes can break on multi-column UPDATEs —
            # only rotate credential + role for an existing row.
            conn.execute(
                """
                UPDATE app_user
                SET password_hash = ?, role = 'admin'
                WHERE id = ?
                """,
                [pwd_hash, int(row[0])],
            )
            print(f"Updated existing user id={row[0]} to admin (email/username unchanged)")
        else:
            next_id = int(
                conn.execute(
                    "SELECT COALESCE(MAX(id), 0) + 1 FROM app_user"
                ).fetchone()[0]
            )
            prefs = json.dumps(
                {
                    "dark_mode": True,
                    "audio_quality": "high",
                    "recommendations_enabled": True,
                    "privacy_public": False,
                }
            )
            conn.execute(
                """
                INSERT INTO app_user
                    (id, username, email, password_hash, role, plan, favorite_genre, created_at, preferences_json)
                VALUES (?, ?, ?, ?, 'admin', 'Premium', 'Pop', ?, ?)
                """,
                [next_id, username, email, pwd_hash, utc_now(), prefs],
            )
            print(f"Created admin id={next_id} email={email} username={username}")

    print("OK — bootstrap complete (password not printed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
