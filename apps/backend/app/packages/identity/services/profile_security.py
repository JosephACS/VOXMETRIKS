"""Profile PIN, trusted devices, and security events — B2C household privacy."""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta
from typing import Any, Dict, List, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.identity.services.password_security import (
    hash_password,
    verify_password,
)
from app.packages.identity.services.user_storage import create_session, ensure_user_tables
from app.packages.personal_subscriptions.domain.errors import (
    PersonalForbiddenError,
    PersonalSubscriptionError,
)

PIN_ALGORITHM = "bcrypt"
WEAK_PINS = frozenset(
    {
        "0000",
        "1111",
        "2222",
        "3333",
        "4444",
        "5555",
        "6666",
        "7777",
        "8888",
        "9999",
        "1234",
        "4321",
        "0123",
        "3210",
        "1122",
        "1212",
        "2121",
        "12345",
        "123456",
        "654321",
        "000000",
        "111111",
    }
)
MAX_PIN_ATTEMPTS = 5
LOCK_MINUTES = 5
DEVICE_TTL_DAYS = 90


class ProfilePinError(PersonalSubscriptionError):
    def __init__(self, message: str, *, code: str = "pin_error"):
        super().__init__(message, code=code)


def ensure_profile_security_tables(conn: duckdb.DuckDBPyConnection) -> None:
    ensure_user_tables(conn)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS profile_pin (
            user_id INTEGER PRIMARY KEY,
            pin_hash VARCHAR NOT NULL,
            algorithm VARCHAR NOT NULL DEFAULT 'bcrypt',
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            require_on_select BOOLEAN NOT NULL DEFAULT TRUE,
            lock_on_switch BOOLEAN NOT NULL DEFAULT TRUE,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until TIMESTAMP,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS trusted_device (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            device_token_hash VARCHAR NOT NULL,
            device_label VARCHAR,
            browser VARCHAR,
            os_name VARCHAR,
            status VARCHAR NOT NULL DEFAULT 'active',
            authorized_at TIMESTAMP NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            last_seen_at TIMESTAMP,
            revoked_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_trusted_device_user
        ON trusted_device(user_id)
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS security_event (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            action VARCHAR NOT NULL,
            summary VARCHAR NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_security_event_user
        ON security_event(user_id, created_at)
        """
    )


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    row = conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()
    return int(row[0])


def _record_event(conn: duckdb.DuckDBPyConnection, user_id: int, action: str, summary: str) -> None:
    ensure_profile_security_tables(conn)
    eid = _next_id(conn, "security_event")
    conn.execute(
        """
        INSERT INTO security_event (id, user_id, action, summary, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [eid, int(user_id), action, summary, utc_now()],
    )


def _validate_pin_format(pin: str) -> str:
    raw = (pin or "").strip()
    if not raw.isdigit() or not (4 <= len(raw) <= 6):
        raise ProfilePinError("El PIN debe tener entre 4 y 6 dígitos", code="pin_invalid")
    if raw in WEAK_PINS or len(set(raw)) == 1:
        raise ProfilePinError("Elige un PIN más seguro", code="pin_weak")
    # Obvious ascending/descending sequences
    asc = "0123456789"
    desc = "9876543210"
    n = len(raw)
    if any(raw == asc[i : i + n] for i in range(len(asc) - n + 1)) or any(
        raw == desc[i : i + n] for i in range(len(desc) - n + 1)
    ):
        raise ProfilePinError("Elige un PIN más seguro", code="pin_weak")
    return raw


def _verify_account_password(conn: duckdb.DuckDBPyConnection, user_id: int, password: str) -> None:
    row = conn.execute(
        "SELECT password_hash FROM app_user WHERE id = ?", [int(user_id)]
    ).fetchone()
    if not row or not verify_password(password or "", str(row[0])):
        raise ProfilePinError("Contraseña incorrecta", code="bad_password")


def get_pin_status(conn: duckdb.DuckDBPyConnection, user_id: int) -> Dict[str, Any]:
    ensure_profile_security_tables(conn)
    row = conn.execute(
        """
        SELECT enabled, require_on_select, lock_on_switch, failed_attempts,
               locked_until, created_at, updated_at
        FROM profile_pin WHERE user_id = ?
        """,
        [int(user_id)],
    ).fetchone()
    if not row:
        return {
            "enabled": False,
            "require_on_select": True,
            "lock_on_switch": True,
            "locked": False,
            "locked_until": None,
        }
    # row: enabled, require_on_select, lock_on_switch, failed_attempts, locked_until, created, updated
    now = utc_now()
    locked = False
    locked_until = row[4]
    if row[0] and locked_until is not None:
        try:
            locked = locked_until > now
        except TypeError:
            locked = str(locked_until) > str(now)
    return {
        "enabled": bool(row[0]),
        "require_on_select": bool(row[1]),
        "lock_on_switch": bool(row[2]),
        "locked": locked,
        "locked_until": str(locked_until) if locked_until else None,
        "created_at": str(row[5]) if row[5] else None,
        "updated_at": str(row[6]) if row[6] else None,
    }


def enable_pin(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    *,
    password: str,
    pin: str,
    pin_confirm: str,
    require_on_select: bool = True,
    lock_on_switch: bool = True,
) -> Dict[str, Any]:
    ensure_profile_security_tables(conn)
    _verify_account_password(conn, user_id, password)
    if pin != pin_confirm:
        raise ProfilePinError("Los PIN no coinciden", code="pin_mismatch")
    pin_n = _validate_pin_format(pin)
    now = utc_now()
    pin_hash = hash_password(pin_n)
    existing = conn.execute(
        "SELECT 1 FROM profile_pin WHERE user_id = ?", [int(user_id)]
    ).fetchone()
    if existing:
        conn.execute(
            """
            UPDATE profile_pin
            SET pin_hash = ?, algorithm = ?, enabled = TRUE,
                require_on_select = ?, lock_on_switch = ?,
                failed_attempts = 0, locked_until = NULL, updated_at = ?
            WHERE user_id = ?
            """,
            [
                pin_hash,
                PIN_ALGORITHM,
                require_on_select,
                lock_on_switch,
                now,
                int(user_id),
            ],
        )
    else:
        conn.execute(
            """
            INSERT INTO profile_pin (
                user_id, pin_hash, algorithm, enabled, require_on_select,
                lock_on_switch, failed_attempts, locked_until, created_at, updated_at
            ) VALUES (?, ?, ?, TRUE, ?, ?, 0, NULL, ?, ?)
            """,
            [
                int(user_id),
                pin_hash,
                PIN_ALGORITHM,
                require_on_select,
                lock_on_switch,
                now,
                now,
            ],
        )
    _record_event(conn, user_id, "pin.enabled", "PIN del perfil activado")
    return get_pin_status(conn, user_id)


def change_pin(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    *,
    password: str,
    pin: str,
    pin_confirm: str,
) -> Dict[str, Any]:
    return enable_pin(
        conn,
        user_id,
        password=password,
        pin=pin,
        pin_confirm=pin_confirm,
    )


def disable_pin(
    conn: duckdb.DuckDBPyConnection, user_id: int, *, password: str
) -> Dict[str, Any]:
    ensure_profile_security_tables(conn)
    _verify_account_password(conn, user_id, password)
    conn.execute(
        """
        UPDATE profile_pin
        SET enabled = FALSE, failed_attempts = 0, locked_until = NULL, updated_at = ?
        WHERE user_id = ?
        """,
        [utc_now(), int(user_id)],
    )
    _record_event(conn, user_id, "pin.disabled", "PIN del perfil desactivado")
    return get_pin_status(conn, user_id)


def reset_pin_with_password(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    *,
    password: str,
    pin: str,
    pin_confirm: str,
) -> Dict[str, Any]:
    status = enable_pin(
        conn,
        user_id,
        password=password,
        pin=pin,
        pin_confirm=pin_confirm,
    )
    _record_event(conn, user_id, "pin.reset", "PIN del perfil restablecido con contraseña")
    return status


def update_pin_preferences(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    *,
    require_on_select: Optional[bool] = None,
    lock_on_switch: Optional[bool] = None,
) -> Dict[str, Any]:
    ensure_profile_security_tables(conn)
    row = conn.execute(
        "SELECT require_on_select, lock_on_switch FROM profile_pin WHERE user_id = ?",
        [int(user_id)],
    ).fetchone()
    if not row:
        raise ProfilePinError("Activa un PIN antes de configurar preferencias", code="pin_missing")
    req = row[0] if require_on_select is None else require_on_select
    lock = row[1] if lock_on_switch is None else lock_on_switch
    conn.execute(
        """
        UPDATE profile_pin
        SET require_on_select = ?, lock_on_switch = ?, updated_at = ?
        WHERE user_id = ?
        """,
        [req, lock, utc_now(), int(user_id)],
    )
    return get_pin_status(conn, user_id)


def _load_pin_row(conn: duckdb.DuckDBPyConnection, user_id: int):
    return conn.execute(
        """
        SELECT pin_hash, enabled, failed_attempts, locked_until
        FROM profile_pin WHERE user_id = ?
        """,
        [int(user_id)],
    ).fetchone()


def verify_pin(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    pin: str,
    *,
    device_token: Optional[str] = None,
    require_trusted_device: bool = False,
) -> Dict[str, Any]:
    ensure_profile_security_tables(conn)
    row = _load_pin_row(conn, user_id)
    if not row or not row[1]:
        raise ProfilePinError("Este perfil no tiene PIN activo", code="pin_missing")
    now = utc_now()
    locked_until = row[3]
    if locked_until is not None:
        try:
            is_locked = locked_until > now
        except TypeError:
            is_locked = str(locked_until) > str(now)
        if is_locked:
            raise ProfilePinError(
                "Este perfil está bloqueado temporalmente por varios intentos incorrectos.",
                code="pin_locked",
            )
    if require_trusted_device:
        if not device_token or not _device_valid(conn, user_id, device_token):
            raise ProfilePinError(
                "Este dispositivo no está autorizado para desbloquear con PIN",
                code="device_required",
            )

    if not verify_password((pin or "").strip(), str(row[0])):
        attempts = int(row[2] or 0) + 1
        locked = None
        if attempts >= MAX_PIN_ATTEMPTS:
            # Progressive lock: 5m, 10m, 15m… based on consecutive failures.
            lock_mult = max(1, attempts // MAX_PIN_ATTEMPTS)
            locked = now + timedelta(minutes=LOCK_MINUTES * lock_mult)
            _record_event(conn, user_id, "pin.locked", "PIN bloqueado temporalmente")
        else:
            _record_event(conn, user_id, "pin.failed", "Intento de PIN incorrecto")
        conn.execute(
            """
            UPDATE profile_pin
            SET failed_attempts = ?, locked_until = ?, updated_at = ?
            WHERE user_id = ?
            """,
            [attempts, locked, now, int(user_id)],
        )
        if locked is not None:
            raise ProfilePinError(
                "Este perfil está bloqueado temporalmente por varios intentos incorrectos.",
                code="pin_locked",
            )
        raise ProfilePinError(
            "El PIN no es correcto. Inténtalo nuevamente.",
            code="pin_incorrect",
        )

    conn.execute(
        """
        UPDATE profile_pin
        SET failed_attempts = 0, locked_until = NULL, updated_at = ?
        WHERE user_id = ?
        """,
        [now, int(user_id)],
    )
    if device_token:
        _touch_device(conn, user_id, device_token)
    return {"ok": True}


def _hash_device_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _device_valid(conn: duckdb.DuckDBPyConnection, user_id: int, device_token: str) -> bool:
    th = _hash_device_token(device_token)
    row = conn.execute(
        """
        SELECT id, expires_at FROM trusted_device
        WHERE user_id = ? AND device_token_hash = ? AND status = 'active'
        LIMIT 1
        """,
        [int(user_id), th],
    ).fetchone()
    if not row:
        return False
    now = utc_now()
    try:
        expired = row[1] is not None and row[1] < now
    except TypeError:
        expired = row[1] is not None and str(row[1]) < str(now)
    if expired:
        conn.execute(
            "UPDATE trusted_device SET status = 'expired', revoked_at = ? WHERE id = ?",
            [now, int(row[0])],
        )
        return False
    return True


def _touch_device(conn: duckdb.DuckDBPyConnection, user_id: int, device_token: str) -> None:
    th = _hash_device_token(device_token)
    conn.execute(
        """
        UPDATE trusted_device SET last_seen_at = ?
        WHERE user_id = ? AND device_token_hash = ? AND status = 'active'
        """,
        [utc_now(), int(user_id), th],
    )


def authorize_device(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    *,
    password: str,
    device_label: Optional[str] = None,
    browser: Optional[str] = None,
    os_name: Optional[str] = None,
) -> Dict[str, Any]:
    ensure_profile_security_tables(conn)
    _verify_account_password(conn, user_id, password)
    token = secrets.token_urlsafe(32)
    th = _hash_device_token(token)
    now = utc_now()
    did = _next_id(conn, "trusted_device")
    conn.execute(
        """
        INSERT INTO trusted_device (
            id, user_id, device_token_hash, device_label, browser, os_name,
            status, authorized_at, expires_at, last_seen_at, revoked_at
        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, NULL)
        """,
        [
            did,
            int(user_id),
            th,
            (device_label or "Este dispositivo")[:120],
            (browser or "")[:80] or None,
            (os_name or "")[:80] or None,
            now,
            now + timedelta(days=DEVICE_TTL_DAYS),
            now,
        ],
    )
    _record_event(conn, user_id, "device.authorized", "Dispositivo autorizado para PIN")
    return {
        "device_id": did,
        "device_token": token,  # shown once — never logged
        "expires_at": str(now + timedelta(days=DEVICE_TTL_DAYS)),
        "allow_pin_unlock": True,
    }


def list_devices(conn: duckdb.DuckDBPyConnection, user_id: int) -> List[Dict[str, Any]]:
    ensure_profile_security_tables(conn)
    rows = conn.execute(
        """
        SELECT id, device_label, browser, os_name, status, authorized_at,
               expires_at, last_seen_at
        FROM trusted_device
        WHERE user_id = ?
        ORDER BY authorized_at DESC
        """,
        [int(user_id)],
    ).fetchall()
    out = []
    for r in rows:
        out.append(
            {
                "id": int(r[0]),
                "device_label": r[1],
                "browser": r[2],
                "os_name": r[3],
                "status": r[4],
                "authorized_at": str(r[5]) if r[5] else None,
                "expires_at": str(r[6]) if r[6] else None,
                "last_seen_at": str(r[7]) if r[7] else None,
            }
        )
    return out


def revoke_device(conn: duckdb.DuckDBPyConnection, user_id: int, device_id: int) -> Dict[str, Any]:
    ensure_profile_security_tables(conn)
    row = conn.execute(
        "SELECT id FROM trusted_device WHERE id = ? AND user_id = ?",
        [int(device_id), int(user_id)],
    ).fetchone()
    if not row:
        raise PersonalForbiddenError("Dispositivo no encontrado")
    conn.execute(
        """
        UPDATE trusted_device
        SET status = 'revoked', revoked_at = ?
        WHERE id = ? AND user_id = ?
        """,
        [utc_now(), int(device_id), int(user_id)],
    )
    _record_event(conn, user_id, "device.revoked", "Dispositivo revocado")
    return {"ok": True}


def revoke_other_devices(
    conn: duckdb.DuckDBPyConnection, user_id: int, *, keep_device_token: Optional[str] = None
) -> Dict[str, Any]:
    ensure_profile_security_tables(conn)
    keep_hash = _hash_device_token(keep_device_token) if keep_device_token else None
    if keep_hash:
        conn.execute(
            """
            UPDATE trusted_device
            SET status = 'revoked', revoked_at = ?
            WHERE user_id = ? AND status = 'active' AND device_token_hash <> ?
            """,
            [utc_now(), int(user_id), keep_hash],
        )
    else:
        conn.execute(
            """
            UPDATE trusted_device
            SET status = 'revoked', revoked_at = ?
            WHERE user_id = ? AND status = 'active'
            """,
            [utc_now(), int(user_id)],
        )
    _record_event(conn, user_id, "device.revoked_others", "Otros dispositivos revocados")
    return {"ok": True}


def revoke_other_sessions(
    conn: duckdb.DuckDBPyConnection, user_id: int, *, keep_token: Optional[str] = None
) -> Dict[str, Any]:
    ensure_user_tables(conn)
    if keep_token:
        conn.execute(
            "DELETE FROM app_session WHERE user_id = ? AND token <> ?",
            [int(user_id), keep_token],
        )
    else:
        conn.execute("DELETE FROM app_session WHERE user_id = ?", [int(user_id)])
    _record_event(conn, user_id, "sessions.revoked", "Sesiones cerradas en otros dispositivos")
    return {"ok": True}


def change_account_password(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    *,
    current_password: str,
    new_password: str,
    confirm_password: str,
    revoke_others: bool = True,
    keep_token: Optional[str] = None,
) -> Dict[str, Any]:
    ensure_user_tables(conn)
    ensure_profile_security_tables(conn)
    _verify_account_password(conn, user_id, current_password)
    if (new_password or "") != (confirm_password or ""):
        raise ProfilePinError("Las contraseñas no coinciden", code="password_mismatch")
    if len(new_password or "") < 4:
        raise ProfilePinError("La nueva contraseña es demasiado corta", code="password_weak")
    if new_password == current_password:
        raise ProfilePinError("La nueva contraseña debe ser distinta", code="password_same")
    common = {"password", "123456", "1234", "qwerty", "demo123", "admin123"}
    if (new_password or "").lower() in common:
        raise ProfilePinError("Elige una contraseña más segura", code="password_weak")

    conn.execute(
        "UPDATE app_user SET password_hash = ? WHERE id = ?",
        [hash_password(new_password), int(user_id)],
    )
    email_row = conn.execute(
        "SELECT email FROM app_user WHERE id = ?", [int(user_id)]
    ).fetchone()
    if email_row:
        conn.execute(
            "DELETE FROM app_email_code WHERE LOWER(email) = ? AND purpose = 'password_reset'",
            [str(email_row[0]).lower()],
        )
    if revoke_others:
        revoke_other_sessions(conn, user_id, keep_token=keep_token)
        # Password change revokes PIN device authorizations (re-auth required).
        conn.execute(
            """
            UPDATE trusted_device
            SET status = 'revoked', revoked_at = ?
            WHERE user_id = ? AND status = 'active'
            """,
            [utc_now(), int(user_id)],
        )
        _record_event(conn, user_id, "device.revoked_others", "Dispositivos PIN revocados tras cambio de contraseña")

    _record_event(conn, user_id, "password.changed", "Contraseña de la cuenta actualizada")
    return {"ok": True, "sessions_revoked": bool(revoke_others)}


def unlock_with_pin_on_device(
    conn: duckdb.DuckDBPyConnection,
    *,
    target_user_id: int,
    pin: str,
    device_token: str,
    remember_days: int = 30,
) -> Dict[str, Any]:
    """Issue a new session for target_user after PIN + trusted device validation.

    Never accepts the caller's identity as the target. Device must belong to target.
    """
    verify_pin(
        conn,
        target_user_id,
        pin,
        device_token=device_token,
        require_trusted_device=True,
    )
    from app.packages.identity.services.user_service import _fetch_user

    user = _fetch_user(conn, int(target_user_id))
    if not user:
        raise PersonalForbiddenError("Usuario no encontrado")
    token = create_session(conn, int(target_user_id), days=remember_days)
    _record_event(
        conn, target_user_id, "pin.unlock", "Perfil desbloqueado con PIN en dispositivo autorizado"
    )
    return {"token": token, "user": user}


def list_security_events(
    conn: duckdb.DuckDBPyConnection, user_id: int, *, limit: int = 30
) -> List[Dict[str, Any]]:
    ensure_profile_security_tables(conn)
    rows = conn.execute(
        """
        SELECT action, summary, created_at
        FROM security_event
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        [int(user_id), int(limit)],
    ).fetchall()
    return [
        {
            "action": r[0],
            "summary": r[1],
            "created_at": str(r[2]) if r[2] else None,
        }
        for r in rows
    ]


def pin_enabled_for_users(
    conn: duckdb.DuckDBPyConnection, user_ids: List[int]
) -> Dict[int, bool]:
    ensure_profile_security_tables(conn)
    if not user_ids:
        return {}
    out = {int(u): False for u in user_ids}
    for uid in user_ids:
        row = conn.execute(
            "SELECT enabled FROM profile_pin WHERE user_id = ?", [int(uid)]
        ).fetchone()
        out[int(uid)] = bool(row and row[0])
    return out
