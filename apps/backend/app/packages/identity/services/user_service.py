"""User auth, profile and preferences."""

from __future__ import annotations

import json
import secrets
from typing import Any, Dict, Optional

import duckdb

from app.core.config import get_settings
from app.core.time_util import utc_now
from app.packages.engagement.services.app_storage import ensure_app_tables
from app.packages.engagement.services.favorite_service import favorite_ids
from app.packages.engagement.services.playlist_service import list_playlists

from .email_service import generate_code, send_verification_email
from .google_auth_service import verify_google_id_token
from .password_security import hash_password, needs_rehash, verify_password
from .user_storage import (
    create_session,
    delete_email_code,
    ensure_user_tables,
    get_email_code,
    increment_email_code_attempts,
    migrate_user_scoping,
    parse_preferences,
    resolve_session,
    revoke_session,
    upsert_email_code,
)


def _next_user_id(conn: duckdb.DuckDBPyConnection) -> int:
    row = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_user").fetchone()
    return int(row[0])


_USER_COLUMNS = (
    "id, username, email, password_hash, role, plan, favorite_genre, "
    "created_at, preferences_json, email_verified, auth_provider"
)


def _user_row_to_dict(row: tuple) -> Dict[str, Any]:
    prefs = parse_preferences(row[8] if len(row) > 8 else "{}")
    return {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "role": row[4] or "user",
        "plan": row[5],
        "favorite_genre": row[6],
        "created_at": str(row[7]) if row[7] else None,
        "preferences": prefs,
        "email_verified": bool(row[9]) if len(row) > 9 and row[9] is not None else True,
        "auth_provider": (row[10] if len(row) > 10 else "local") or "local",
    }


def _fetch_user(conn: duckdb.DuckDBPyConnection, user_id: int) -> Optional[Dict[str, Any]]:
    ensure_user_tables(conn)
    row = conn.execute(
        f"SELECT {_USER_COLUMNS} FROM app_user WHERE id = ?",
        [user_id],
    ).fetchone()
    if not row:
        return None
    return _user_row_to_dict(row)


def _unique_username(conn: duckdb.DuckDBPyConnection, base: str) -> str:
    """Return a username derived from ``base`` that is not yet taken."""
    cleaned = "".join(ch for ch in base.strip().lower() if ch.isalnum() or ch in "._-")
    cleaned = cleaned[:24] or "user"
    if len(cleaned) < 3:
        cleaned = (cleaned + "user")[:5]
    candidate = cleaned
    while conn.execute(
        "SELECT 1 FROM app_user WHERE LOWER(username) = ?", [candidate.lower()]
    ).fetchone():
        candidate = f"{cleaned}{secrets.randbelow(9000) + 1000}"
    return candidate


def _insert_user(
    conn: duckdb.DuckDBPyConnection,
    *,
    username: str,
    email: str,
    password_hash: str,
    favorite_genre: Optional[str],
    email_verified: bool,
    auth_provider: str = "local",
) -> int:
    new_id = _next_user_id(conn)
    prefs = json.dumps({
        "dark_mode": True,
        "audio_quality": "high",
        "recommendations_enabled": True,
        "privacy_public": False,
    })
    conn.execute(
        """
        INSERT INTO app_user
            (id, username, email, password_hash, role, plan, favorite_genre,
             created_at, preferences_json, email_verified, auth_provider)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            new_id, username, email, password_hash, "user", "Free",
            favorite_genre, utc_now(), prefs, email_verified, auth_provider,
        ],
    )
    return new_id


def login(
    conn: duckdb.DuckDBPyConnection,
    login_id: str,
    password: str,
    remember: bool = True,
) -> Optional[Dict[str, Any]]:
    ensure_user_tables(conn)
    migrate_user_scoping(conn)
    login_id = login_id.strip().lower()
    row = conn.execute(
        f"""
        SELECT {_USER_COLUMNS}
        FROM app_user
        WHERE LOWER(email) = ? OR LOWER(username) = ?
        """,
        [login_id, login_id],
    ).fetchone()
    if not row or not verify_password(password, row[3]):
        return None
    user = _user_row_to_dict(row)
    user_id = int(row[0])
    if not user["email_verified"]:
        # Caller maps this to a 403 so the UI can prompt for the code.
        return {"verification_required": True, "email": user["email"]}
    if needs_rehash(row[3]):
        conn.execute(
            "UPDATE app_user SET password_hash = ? WHERE id = ?",
            [hash_password(password), user_id],
        )
    days = 90 if remember else 1
    token = create_session(conn, user_id, days=days)
    return {"token": token, "user": user}


def _issue_verification_code(conn: duckdb.DuckDBPyConnection, email: str) -> Dict[str, Any]:
    """Generate, store and email a code. Returns dev metadata for the route."""
    cfg = get_settings()
    code = generate_code()
    upsert_email_code(
        conn, email, hash_password(code),
        purpose="verify", ttl_minutes=cfg.email_code_ttl_min,
    )
    sent = send_verification_email(email, code)
    out: Dict[str, Any] = {
        "verification_required": True,
        "email": email,
        "email_sent": sent,
    }
    # Dev mode (no SMTP configured): surface the code so localhost can test.
    # Never expose the code in production, even if SMTP is misconfigured.
    if not cfg.email_enabled and not cfg.is_production:
        out["dev_code"] = code
    return out


def register(
    conn: duckdb.DuckDBPyConnection,
    username: str,
    email: str,
    password: str,
    favorite_genre: Optional[str] = None,
) -> Dict[str, Any]:
    ensure_user_tables(conn)
    migrate_user_scoping(conn)
    username = username.strip()
    email = email.strip().lower()
    if len(username) < 3:
        raise ValueError("username must be at least 3 characters")
    if len(password) < 4:
        raise ValueError("password must be at least 4 characters")

    existing = conn.execute(
        f"SELECT {_USER_COLUMNS} FROM app_user WHERE LOWER(email) = ? OR LOWER(username) = ?",
        [email, username.lower()],
    ).fetchone()
    if existing:
        ex = _user_row_to_dict(existing)
        # Allow re-registration only for the same email that never verified.
        if ex["email"].lower() == email and not ex["email_verified"]:
            conn.execute(
                "UPDATE app_user SET username = ?, password_hash = ?, favorite_genre = ? WHERE id = ?",
                [username, hash_password(password), favorite_genre, ex["id"]],
            )
            return _issue_verification_code(conn, email)
        raise ValueError("email or username already exists")

    _insert_user(
        conn,
        username=username,
        email=email,
        password_hash=hash_password(password),
        favorite_genre=favorite_genre,
        email_verified=False,
        auth_provider="local",
    )
    return _issue_verification_code(conn, email)


def verify_email(
    conn: duckdb.DuckDBPyConnection, email: str, code: str
) -> Optional[Dict[str, Any]]:
    """Validate a sign-up code. Returns {token, user} on success, else raises."""
    ensure_user_tables(conn)
    email = email.strip().lower()
    code = (code or "").strip()
    record = get_email_code(conn, email)
    if not record:
        raise ValueError("no pending verification for this email")
    if record["expires_at"] and record["expires_at"] < utc_now():
        delete_email_code(conn, email)
        raise ValueError("code expired, request a new one")
    if record["attempts"] >= get_settings().email_code_max_attempts:
        delete_email_code(conn, email)
        raise ValueError("too many attempts, request a new code")
    if not verify_password(code, record["code_hash"]):
        increment_email_code_attempts(conn, email)
        raise ValueError("invalid code")

    conn.execute(
        "UPDATE app_user SET email_verified = TRUE WHERE LOWER(email) = ?", [email]
    )
    delete_email_code(conn, email)
    row = conn.execute(
        f"SELECT {_USER_COLUMNS} FROM app_user WHERE LOWER(email) = ?", [email]
    ).fetchone()
    if not row:
        raise ValueError("user not found")
    user = _user_row_to_dict(row)
    token = create_session(conn, int(row[0]), days=90)
    return {"token": token, "user": user}


def resend_verification(conn: duckdb.DuckDBPyConnection, email: str) -> Dict[str, Any]:
    ensure_user_tables(conn)
    email = email.strip().lower()
    row = conn.execute(
        "SELECT email_verified FROM app_user WHERE LOWER(email) = ?", [email]
    ).fetchone()
    if not row:
        raise ValueError("no account for this email")
    if bool(row[0]):
        raise ValueError("email already verified")
    return _issue_verification_code(conn, email)


def google_login(conn: duckdb.DuckDBPyConnection, credential: str) -> Optional[Dict[str, Any]]:
    """Sign in (or auto-register) via a Google ID token."""
    ensure_user_tables(conn)
    migrate_user_scoping(conn)
    claims = verify_google_id_token(credential)
    if not claims:
        return None
    email = claims["email"]
    row = conn.execute(
        f"SELECT {_USER_COLUMNS} FROM app_user WHERE LOWER(email) = ?", [email]
    ).fetchone()
    if row:
        user_id = int(row[0])
        # Google verified the email — clear any pending local verification.
        conn.execute(
            "UPDATE app_user SET email_verified = TRUE WHERE id = ?", [user_id]
        )
        delete_email_code(conn, email)
        user = _fetch_user(conn, user_id)
    else:
        base = claims.get("name") or email.split("@", 1)[0]
        username = _unique_username(conn, base)
        # Random unusable password — this account signs in via Google.
        random_pw = hash_password(secrets.token_urlsafe(24))
        user_id = _insert_user(
            conn,
            username=username,
            email=email,
            password_hash=random_pw,
            favorite_genre=None,
            email_verified=True,
            auth_provider="google",
        )
        user = _fetch_user(conn, user_id)
    token = create_session(conn, user_id, days=90)
    return {"token": token, "user": user}


def get_me(conn: duckdb.DuckDBPyConnection, user_id: int) -> Optional[Dict[str, Any]]:
    user = _fetch_user(conn, user_id)
    if not user:
        return None
    ensure_app_tables(conn)
    migrate_user_scoping(conn)
    fav_count = len(favorite_ids(conn, user_id))
    playlists = [p for p in list_playlists(conn, user_id)]
    profile = {
        **user,
        "stats": {
            "favorites_count": fav_count,
            "playlists_count": len(playlists),
        },
        "playlists": playlists[:6],
    }
    return profile


def update_preferences(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    user = _fetch_user(conn, user_id)
    if not user:
        return None
    pref_keys = {"dark_mode", "audio_quality", "recommendations_enabled", "privacy_public"}
    pref_updates = {k: updates[k] for k in pref_keys if k in updates}
    prefs = {**user.get("preferences", {}), **pref_updates}
    favorite_genre = updates.get("favorite_genre", user.get("favorite_genre"))
    conn.execute(
        """
        UPDATE app_user
        SET preferences_json = ?, favorite_genre = COALESCE(?, favorite_genre)
        WHERE id = ?
        """,
        [json.dumps(prefs), updates.get("favorite_genre"), user_id],
    )
    return _fetch_user(conn, user_id)


def get_user_id_from_token(conn: duckdb.DuckDBPyConnection, token: str) -> Optional[int]:
    return resolve_session(conn, token)


def logout(conn: duckdb.DuckDBPyConnection, token: str) -> None:
    revoke_session(conn, token)
