"""DuckDB tables for users, sessions and preferences."""

from __future__ import annotations

import json
import uuid
from datetime import timedelta
from typing import Any, Dict, Optional

import duckdb

from app.core.time_util import utc_now
from app.core.config import get_settings
from app.core.database import get_table_columns, table_exists
from .password_security import hash_password


def ensure_user_tables(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_user (
            id              INTEGER PRIMARY KEY,
            username        VARCHAR NOT NULL UNIQUE,
            email           VARCHAR NOT NULL UNIQUE,
            password_hash   VARCHAR NOT NULL,
            role            VARCHAR DEFAULT 'user',
            plan            VARCHAR DEFAULT 'Free',
            favorite_genre  VARCHAR,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            preferences_json VARCHAR DEFAULT '{}'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_session (
            token       VARCHAR PRIMARY KEY,
            user_id     INTEGER NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at  TIMESTAMP
        )
    """)
    _migrate_user_role(conn)
    _seed_demo_users(conn)


def _migrate_user_role(conn: duckdb.DuckDBPyConnection) -> None:
    cols = get_table_columns(conn, "app_user")
    if "role" not in cols:
        conn.execute("ALTER TABLE app_user ADD COLUMN role VARCHAR DEFAULT 'user'")
    conn.execute(
        """
        UPDATE app_user
        SET role = CASE
            WHEN LOWER(username) = 'admin' THEN 'engineer'
            ELSE COALESCE(role, 'user')
        END
        WHERE role IS NULL OR LOWER(username) = 'admin'
        """
    )


def _seed_demo_users(conn: duckdb.DuckDBPyConnection) -> None:
    if not get_settings().seed_demo_users:
        return
    defaults = [
        ("demo", "demo@voxmetrik.io", "demo123", "user", "Premium", "Pop"),
        ("admin", "admin@voxmetrik.io", "admin123", "engineer", "Premium", "Rock"),
    ]
    for username, email, pwd, role, plan, genre in defaults:
        row = conn.execute(
            "SELECT 1 FROM app_user WHERE email = ?", [email]
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE app_user SET role = ? WHERE LOWER(username) = ?",
                [role, username.lower()],
            )
            continue
        next_id = conn.execute(
            "SELECT COALESCE(MAX(id), 0) + 1 FROM app_user"
        ).fetchone()[0]
        prefs = json.dumps({
            "dark_mode": True,
            "audio_quality": "high",
            "recommendations_enabled": True,
            "privacy_public": False,
        })
        conn.execute(
            """
            INSERT INTO app_user
                (id, username, email, password_hash, role, plan, favorite_genre, created_at, preferences_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                int(next_id), username, email, hash_password(pwd),
                role, plan, genre, utc_now(), prefs,
            ],
        )


def migrate_user_scoping(conn: duckdb.DuckDBPyConnection) -> None:
    """Add user_id to playlists/favorites for per-user data."""
    if table_exists(conn, "app_playlist"):
        cols = get_table_columns(conn, "app_playlist")
        if "user_id" not in cols:
            conn.execute(
                "ALTER TABLE app_playlist ADD COLUMN user_id INTEGER DEFAULT 1"
            )

    if not table_exists(conn, "app_favorite"):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS app_favorite (
                user_id  INTEGER NOT NULL DEFAULT 1,
                track_id INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, track_id)
            )
        """)
        return

    cols = get_table_columns(conn, "app_favorite")
    if "user_id" in cols:
        return

    conn.execute("""
        CREATE TABLE app_favorite_new (
            user_id  INTEGER NOT NULL DEFAULT 1,
            track_id INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, track_id)
        )
    """)
    conn.execute(
        "INSERT INTO app_favorite_new (track_id, added_at) SELECT track_id, added_at FROM app_favorite"
    )
    conn.execute("DROP TABLE app_favorite")
    conn.execute("ALTER TABLE app_favorite_new RENAME TO app_favorite")


def create_session(
    conn: duckdb.DuckDBPyConnection, user_id: int, days: int = 30
) -> str:
    ensure_user_tables(conn)
    token = str(uuid.uuid4())
    expires = utc_now() + timedelta(days=days)
    conn.execute(
        "INSERT INTO app_session (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        [token, user_id, utc_now(), expires],
    )
    return token


def revoke_session(conn: duckdb.DuckDBPyConnection, token: str) -> None:
    ensure_user_tables(conn)
    conn.execute("DELETE FROM app_session WHERE token = ?", [token])


def resolve_session(conn: duckdb.DuckDBPyConnection, token: str) -> Optional[int]:
    ensure_user_tables(conn)
    row = conn.execute(
        """
        SELECT user_id FROM app_session
        WHERE token = ? AND (expires_at IS NULL OR expires_at > ?)
        """,
        [token, utc_now()],
    ).fetchone()
    return int(row[0]) if row else None


def parse_preferences(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}
