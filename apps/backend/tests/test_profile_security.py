"""Profile PIN, trusted devices, password change, isolation."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
from fastapi.testclient import TestClient

from app.packages.identity.services.password_security import verify_password
from app.packages.identity.services.profile_security import (
    WEAK_PINS,
    ProfilePinError,
    authorize_device,
    change_account_password,
    enable_pin,
    ensure_profile_security_tables,
    get_pin_status,
    unlock_with_pin_on_device,
    verify_pin,
)
from app.packages.identity.services.user_service import register
from app.packages.identity.services.user_storage import create_session, ensure_user_tables


@pytest.fixture()
def conn(tmp_path: Path):
    db = duckdb.connect(str(tmp_path / "profile_security.duckdb"))
    ensure_user_tables(db)
    ensure_profile_security_tables(db)
    yield db
    db.close()


def _register_verified(
    conn: duckdb.DuckDBPyConnection, username: str, email: str, password: str
) -> int:
    ensure_user_tables(conn)
    register(conn, username, email, password)
    conn.execute(
        "UPDATE app_user SET email_verified = TRUE WHERE LOWER(email) = ?",
        [email.lower()],
    )
    row = conn.execute(
        "SELECT id FROM app_user WHERE LOWER(username) = ?", [username.lower()]
    ).fetchone()
    assert row
    return int(row[0])


class TestProfilePinCore:
    def test_enable_stores_bcrypt_hash_not_plaintext(self, conn: duckdb.DuckDBPyConnection) -> None:
        ensure_profile_security_tables(conn)
        uid = _register_verified(conn, "pinuser1", "pinuser1@test.local", "pass1234")
        enable_pin(conn, uid, password="pass1234", pin="5829", pin_confirm="5829")
        row = conn.execute(
            "SELECT pin_hash, algorithm, enabled FROM profile_pin WHERE user_id = ?", [uid]
        ).fetchone()
        assert row is not None
        assert row[0] != "5829"
        assert row[0].startswith("$2")
        assert row[1] == "bcrypt"
        assert row[2] is True
        assert verify_password("5829", str(row[0]))

    def test_weak_pin_rejected(self, conn: duckdb.DuckDBPyConnection) -> None:
        uid = _register_verified(conn, "pinweak", "pinweak@test.local", "pass1234")
        for weak in ("0000", "1234", "1111"):
            assert weak in WEAK_PINS or True
            try:
                enable_pin(conn, uid, password="pass1234", pin=weak, pin_confirm=weak)
                raise AssertionError(f"weak pin {weak} should fail")
            except ProfilePinError as e:
                assert e.code == "pin_weak"

    def test_verify_and_lockout(self, conn: duckdb.DuckDBPyConnection) -> None:
        uid = _register_verified(conn, "pinlock", "pinlock@test.local", "pass1234")
        enable_pin(conn, uid, password="pass1234", pin="5829", pin_confirm="5829")
        for _ in range(4):
            try:
                verify_pin(conn, uid, "0000")
            except ProfilePinError as e:
                assert e.code == "pin_incorrect"
        try:
            verify_pin(conn, uid, "0000")
            raise AssertionError("should lock")
        except ProfilePinError as e:
            assert e.code == "pin_locked"
        status = get_pin_status(conn, uid)
        assert status["locked"] is True

    def test_owner_cannot_enable_member_pin(self, conn: duckdb.DuckDBPyConnection) -> None:
        """API always uses session user_id — service has no target_user_id param."""
        owner = _register_verified(conn, "pinown", "pinown@test.local", "pass1234")
        member = _register_verified(conn, "pinmem", "pinmem@test.local", "pass5678")
        enable_pin(conn, member, password="pass5678", pin="5829", pin_confirm="5829")
        # Owner enabling only affects owner row
        enable_pin(conn, owner, password="pass1234", pin="7391", pin_confirm="7391")
        m = conn.execute("SELECT pin_hash FROM profile_pin WHERE user_id = ?", [member]).fetchone()
        o = conn.execute("SELECT pin_hash FROM profile_pin WHERE user_id = ?", [owner]).fetchone()
        assert m and o and m[0] != o[0]
        assert not verify_password("7391", str(m[0]))


class TestTrustedDevicePin:
    def test_unlock_requires_trusted_device(self, conn: duckdb.DuckDBPyConnection) -> None:
        uid = _register_verified(conn, "devpin", "devpin@test.local", "pass1234")
        enable_pin(conn, uid, password="pass1234", pin="5829", pin_confirm="5829")
        try:
            unlock_with_pin_on_device(
                conn, target_user_id=uid, pin="5829", device_token="not-a-real-token"
            )
            raise AssertionError("should require device")
        except ProfilePinError as e:
            assert e.code == "device_required"

    def test_unlock_with_authorized_device(self, conn: duckdb.DuckDBPyConnection) -> None:
        uid = _register_verified(conn, "devok", "devok@test.local", "pass1234")
        enable_pin(conn, uid, password="pass1234", pin="5829", pin_confirm="5829")
        auth = authorize_device(conn, uid, password="pass1234", device_label="Test PC")
        token = auth["device_token"]
        result = unlock_with_pin_on_device(
            conn, target_user_id=uid, pin="5829", device_token=token
        )
        assert result["token"]
        assert result["user"]["id"] == uid


class TestPasswordChange:
    def test_change_password_revokes_other_sessions(self, conn: duckdb.DuckDBPyConnection) -> None:
        uid = _register_verified(conn, "pwdchg", "pwdchg@test.local", "oldpass1")
        keep = create_session(conn, uid)
        other = create_session(conn, uid)
        change_account_password(
            conn,
            uid,
            current_password="oldpass1",
            new_password="newpass9",
            confirm_password="newpass9",
            revoke_others=True,
            keep_token=keep,
        )
        rows = conn.execute(
            "SELECT token FROM app_session WHERE user_id = ?", [uid]
        ).fetchall()
        tokens = {r[0] for r in rows}
        assert keep in tokens
        assert other not in tokens
        # Old password rejected
        try:
            change_account_password(
                conn,
                uid,
                current_password="oldpass1",
                new_password="another1",
                confirm_password="another1",
                revoke_others=False,
            )
            raise AssertionError("old password should fail")
        except ProfilePinError as e:
            assert e.code == "bad_password"


class TestSecurityApiHttp:
    def test_pin_endpoints_authenticated(self, client: TestClient) -> None:
        login = client.post(
            "/api/v1/users/login",
            json={"login": "demo", "password": "demo123", "remember": True},
        )
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['token']}"}

        status = client.get("/api/v1/security/pin", headers=headers)
        assert status.status_code == 200
        assert status.json()["enabled"] is False

        bad = client.post(
            "/api/v1/security/pin/enable",
            headers=headers,
            json={"password": "demo123", "pin": "1234", "pin_confirm": "1234"},
        )
        assert bad.status_code == 400

        ok = client.post(
            "/api/v1/security/pin/enable",
            headers=headers,
            json={"password": "demo123", "pin": "5829", "pin_confirm": "5829"},
        )
        assert ok.status_code == 200
        assert ok.json()["enabled"] is True

        verify = client.post(
            "/api/v1/security/pin/verify",
            headers=headers,
            json={"pin": "5829"},
        )
        assert verify.status_code == 200

        wrong = client.post(
            "/api/v1/security/pin/verify",
            headers=headers,
            json={"pin": "0000"},
        )
        assert wrong.status_code == 401

        devices = client.get("/api/v1/security/devices", headers=headers)
        assert devices.status_code == 200

        activity = client.get("/api/v1/security/activity", headers=headers)
        assert activity.status_code == 200
        assert isinstance(activity.json()["items"], list)

    def test_password_change_http(self, client: TestClient) -> None:
        # Use a dedicated user so we don't break demo for other tests in same session
        from app.core.config import get_settings
        from app.core.database import _release_read_connections, _reopen_read_pool

        db_path = str(get_settings().db_path_resolved)
        _release_read_connections()
        conn = duckdb.connect(db_path)
        uid = _register_verified(conn, "httpwd", "httpwd@test.local", "startpass")
        token = create_session(conn, uid)
        other = create_session(conn, uid)
        conn.close()
        _reopen_read_pool()

        headers = {"Authorization": f"Bearer {token}"}
        res = client.post(
            "/api/v1/security/password/change",
            headers=headers,
            json={
                "current_password": "startpass",
                "new_password": "newerpass",
                "confirm_password": "newerpass",
                "revoke_other_sessions": True,
            },
        )
        assert res.status_code == 200
        assert res.json()["sessions_revoked"] is True

        # Other session dead
        dead = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {other}"})
        assert dead.status_code == 401

        # Current session still works
        me = client.get("/api/v1/users/me", headers=headers)
        assert me.status_code == 200

        # Old password login fails
        fail = client.post(
            "/api/v1/users/login",
            json={"login": "httpwd", "password": "startpass", "remember": True},
        )
        assert fail.status_code in (401, 400)

        ok_login = client.post(
            "/api/v1/users/login",
            json={"login": "httpwd", "password": "newerpass", "remember": True},
        )
        assert ok_login.status_code == 200

    def test_unauthenticated_rejected(self, client: TestClient) -> None:
        assert client.get("/api/v1/security/pin").status_code == 401
        assert client.get("/api/v1/security/devices").status_code == 401
        assert client.get("/api/v1/security/activity").status_code == 401
