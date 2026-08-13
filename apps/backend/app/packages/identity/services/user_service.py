"""User auth, profile and preferences."""

from __future__ import annotations

import json
import secrets
from typing import Any, Dict, Optional

import duckdb

from app.core.config import get_settings
from app.core.email_format import is_valid_email_format
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
    try:
        from app.packages.personal_subscriptions.application.use_cases import (
            ensure_free_subscription,
        )

        ensure_free_subscription(conn, user_id)
    except Exception:  # noqa: BLE001
        pass
    if needs_rehash(row[3]):
        conn.execute(
            "UPDATE app_user SET password_hash = ? WHERE id = ?",
            [hash_password(password), user_id],
        )
    days = 90 if remember else 1
    token = create_session(conn, user_id, days=days)
    return {"token": token, "user": user}


def _issue_verification_code(conn: duckdb.DuckDBPyConnection, email: str) -> Dict[str, Any]:
    """Generate, store and email a code. Returns delivery metadata for the route."""
    cfg = get_settings()
    existing = get_email_code(conn, email, purpose="verify")
    if existing and existing.get("created_at"):
        age = (utc_now() - existing["created_at"]).total_seconds()
        if age < cfg.email_resend_cooldown_sec:
            return {
                "verification_required": True,
                "email": email,
                "email_sent": False,
                "provider": cfg.email_provider,
                "rate_limited": True,
                "retry_after_sec": int(cfg.email_resend_cooldown_sec - age),
            }

    code = generate_code()
    upsert_email_code(
        conn, email, hash_password(code),
        purpose="verify", ttl_minutes=cfg.email_code_ttl_min,
    )
    delivery = send_verification_email(email, code, conn=conn)
    out: Dict[str, Any] = {
        "verification_required": True,
        "email": email,
        "email_sent": bool(delivery.get("email_sent")),
        "provider": delivery.get("provider") or cfg.email_provider,
        "rate_limited": False,
    }
    if cfg.email_is_console and not cfg.is_production:
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
    if len(username) > 64:
        raise ValueError("username must be at most 64 characters")
    if not is_valid_email_format(email):
        raise ValueError("invalid email format")
    if len(password) < 4:
        raise ValueError("password must be at least 4 characters")
    if len(password) > 128:
        raise ValueError("password must be at most 128 characters")

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
    record = get_email_code(conn, email, purpose="verify")
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
    try:
        from app.packages.personal_subscriptions.application.use_cases import (
            ensure_free_subscription,
        )

        ensure_free_subscription(conn, int(user["id"]))
    except Exception:  # noqa: BLE001 — Free assign must not block login
        pass
    token = create_session(conn, int(row[0]), days=90)
    return {"token": token, "user": user}


def resend_verification(conn: duckdb.DuckDBPyConnection, email: str) -> Dict[str, Any]:
    """Resend verification. Generic success for unknown emails (anti-enumeration)."""
    ensure_user_tables(conn)
    email = email.strip().lower()
    row = conn.execute(
        "SELECT email_verified FROM app_user WHERE LOWER(email) = ?", [email]
    ).fetchone()
    generic = {
        "ok": True,
        "email": email,
        "email_sent": False,
        "message": "If an unverified account exists, a code was sent.",
    }
    if not row:
        return generic
    if bool(row[0]):
        return {**generic, "message": "If an unverified account exists, a code was sent."}
    issued = _issue_verification_code(conn, email)
    return {
        "ok": True,
        "email": email,
        "email_sent": issued.get("email_sent", False),
        "provider": issued.get("provider"),
        "rate_limited": issued.get("rate_limited", False),
        "retry_after_sec": issued.get("retry_after_sec"),
        "dev_code": issued.get("dev_code"),
        "message": "If an unverified account exists, a code was sent.",
        "verification_required": True,
    }


def request_password_reset(conn: duckdb.DuckDBPyConnection, email: str) -> Dict[str, Any]:
    """Issue a one-time reset code. Always returns a generic response."""
    from app.packages.platform_ops.application.email_service import send_rendered_email
    from app.packages.platform_ops.application.email_templates import password_reset_email

    ensure_user_tables(conn)
    cfg = get_settings()
    email = email.strip().lower()
    generic = {
        "ok": True,
        "message": "If an account exists for that email, reset instructions were sent.",
    }
    row = conn.execute(
        "SELECT id FROM app_user WHERE LOWER(email) = ?", [email]
    ).fetchone()
    if not row:
        return generic

    existing = get_email_code(conn, email, purpose="password_reset")
    if existing and existing.get("created_at"):
        age = (utc_now() - existing["created_at"]).total_seconds()
        if age < cfg.email_resend_cooldown_sec:
            return {
                **generic,
                "rate_limited": True,
                "retry_after_sec": int(cfg.email_resend_cooldown_sec - age),
            }

    code = generate_code(length=8)
    upsert_email_code(
        conn, email, hash_password(code),
        purpose="password_reset", ttl_minutes=cfg.password_reset_ttl_min,
    )
    reset_url = None
    base = cfg.resolved_frontend_base_url
    if base:
        reset_url = f"{base}/login?mode=reset"
    rendered = password_reset_email(
        code=code,
        expires_min=cfg.password_reset_ttl_min,
        reset_url=reset_url,
        locale="es",
    )
    result = send_rendered_email(
        to_address=email,
        rendered=rendered,
        conn=conn,
        related_type="password_reset",
        related_id=email,
    )
    out = {
        **generic,
        "email_sent": bool(result.success),
        "provider": result.provider_code,
        "console": bool(result.labeled_mock),
    }
    if cfg.email_is_console and not cfg.is_production:
        out["dev_code"] = code
    return out


def reset_password(
    conn: duckdb.DuckDBPyConnection,
    email: str,
    code: str,
    new_password: str,
) -> Dict[str, Any]:
    """Consume a one-time reset code and set a new password atomically.

    Defensive validation mutations (attempt increments, expired/max-attempt
    deletions) commit before the client-facing error is raised. The successful
    password change + session/device revocation remains a single transaction.
    """
    from app.core.database import transactional
    from app.packages.identity.services.profile_security import (
        _record_event,
        ensure_profile_security_tables,
    )

    ensure_user_tables(conn)
    email = email.strip().lower()
    code = (code or "").strip()
    if len(new_password or "") < 4:
        raise ValueError("password must be at least 4 characters")

    # Phase 1: commit defensive validation side-effects, then raise outside.
    client_error: Optional[str] = None
    with transactional(conn):
        record = get_email_code(conn, email, purpose="password_reset")
        if not record:
            client_error = "invalid or expired reset code"
        elif record["expires_at"] and record["expires_at"] < utc_now():
            delete_email_code(conn, email)
            client_error = "invalid or expired reset code"
        elif record["attempts"] >= get_settings().email_code_max_attempts:
            delete_email_code(conn, email)
            client_error = "too many attempts, request a new code"
        elif not verify_password(code, record["code_hash"]):
            increment_email_code_attempts(conn, email)
            client_error = "invalid or expired reset code"
        else:
            user_row = conn.execute(
                "SELECT id FROM app_user WHERE LOWER(email) = ?", [email]
            ).fetchone()
            if not user_row:
                delete_email_code(conn, email)
                client_error = "invalid or expired reset code"

    if client_error:
        raise ValueError(client_error)

    # Phase 2: atomic success path (re-check under the same transactional lock).
    # Validation side-effects commit; revoke failures roll the whole success work back.
    client_error = None
    with transactional(conn):
        record = get_email_code(conn, email, purpose="password_reset")
        if not record:
            client_error = "invalid or expired reset code"
        elif record["expires_at"] and record["expires_at"] < utc_now():
            delete_email_code(conn, email)
            client_error = "invalid or expired reset code"
        elif record["attempts"] >= get_settings().email_code_max_attempts:
            delete_email_code(conn, email)
            client_error = "too many attempts, request a new code"
        elif not verify_password(code, record["code_hash"]):
            increment_email_code_attempts(conn, email)
            client_error = "invalid or expired reset code"
        else:
            user_row = conn.execute(
                "SELECT id FROM app_user WHERE LOWER(email) = ?", [email]
            ).fetchone()
            if not user_row:
                delete_email_code(conn, email)
                client_error = "invalid or expired reset code"
            else:
                user_id = int(user_row[0])
                conn.execute(
                    "UPDATE app_user SET password_hash = ? WHERE id = ?",
                    [hash_password(new_password), user_id],
                )
                delete_email_code(conn, email)
                # Password recovery invalidates every browser session and trusted device.
                conn.execute("DELETE FROM app_session WHERE user_id = ?", [user_id])
                ensure_profile_security_tables(conn)
                conn.execute(
                    """
                    UPDATE trusted_device
                    SET status = 'revoked', revoked_at = ?
                    WHERE user_id = ? AND status = 'active'
                    """,
                    [utc_now(), user_id],
                )
                _record_event(
                    conn, user_id, "password.reset", "Password reset; sessions revoked"
                )

                sessions_left = int(
                    conn.execute(
                        "SELECT COUNT(*) FROM app_session WHERE user_id = ?", [user_id]
                    ).fetchone()[0]
                )
                devices_active = int(
                    conn.execute(
                        "SELECT COUNT(*) FROM trusted_device "
                        "WHERE user_id = ? AND status = 'active'",
                        [user_id],
                    ).fetchone()[0]
                )
                if sessions_left or devices_active:
                    raise RuntimeError(
                        "password reset failed to revoke all sessions/devices"
                    )

    if client_error:
        raise ValueError(client_error)

    return {"ok": True, "message": "Password updated"}


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
