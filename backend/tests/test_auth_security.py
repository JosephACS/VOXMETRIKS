"""Auth security — bcrypt migration, server logout, health exposure."""

from __future__ import annotations

import hashlib
import os

import duckdb
from fastapi.testclient import TestClient

from app.packages.users.services.password_security import (
    hash_password,
    is_legacy_hash,
    verify_password,
)
from app.packages.users.services.user_storage import ensure_user_tables


class TestPasswordSecurity:
    def test_bcrypt_hash_and_verify(self) -> None:
        stored = hash_password("secret123")
        assert stored.startswith("$2")
        assert verify_password("secret123", stored)
        assert not verify_password("wrong", stored)

    def test_legacy_sha256_still_verifies(self) -> None:
        legacy = hashlib.sha256(b"demo123").hexdigest()
        assert is_legacy_hash(legacy)
        assert verify_password("demo123", legacy)


class TestServerLogout:
    def test_logout_invalidates_token(self, client: TestClient) -> None:
        login = client.post(
            "/api/v1/users/login",
            json={"login": "demo", "password": "demo123", "remember": True},
        )
        assert login.status_code == 200
        token = login.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/api/v1/users/me", headers=headers)
        assert me.status_code == 200

        logout = client.post("/api/v1/users/logout", headers=headers)
        assert logout.status_code == 200
        assert logout.json()["ok"] is True

        me_after = client.get("/api/v1/users/me", headers=headers)
        assert me_after.status_code == 401

    def test_logout_without_token_is_idempotent(self, client: TestClient) -> None:
        response = client.post("/api/v1/users/logout")
        assert response.status_code == 200
        assert response.json()["ok"] is True


class TestPasswordRehashOnLogin:
    def test_legacy_password_upgraded_to_bcrypt(self, client: TestClient) -> None:
        from app.core.config import get_settings

        db_path = os.environ["DB_PATH"]
        legacy = hashlib.sha256(b"demo123").hexdigest()
        conn = duckdb.connect(db_path)
        ensure_user_tables(conn)
        conn.execute(
            "UPDATE app_user SET password_hash = ? WHERE LOWER(username) = ?",
            [legacy, "demo"],
        )
        conn.close()

        response = client.post(
            "/api/v1/users/login",
            json={"login": "demo", "password": "demo123", "remember": True},
        )
        assert response.status_code == 200

        conn = duckdb.connect(db_path)
        ensure_user_tables(conn)
        row = conn.execute(
            "SELECT password_hash FROM app_user WHERE LOWER(username) = ?",
            ["demo"],
        ).fetchone()
        conn.close()
        assert row is not None
        assert row[0].startswith("$2")

        conn = duckdb.connect(db_path)
        ensure_user_tables(conn)
        conn.execute(
            "UPDATE app_user SET password_hash = ? WHERE LOWER(username) = ?",
            [hash_password("demo123"), "demo"],
        )
        conn.close()
        get_settings.cache_clear()


class TestEmailVerificationFlow:
    def test_register_requires_code_then_verifies(self, client: TestClient) -> None:
        email = "newuser@voxmetrik.io"
        reg = client.post(
            "/api/v1/users/register",
            json={
                "username": "newuser",
                "email": email,
                "password": "secret123",
                "favorite_genre": "Pop",
            },
        )
        assert reg.status_code == 201, reg.text
        body = reg.json()
        assert body["verification_required"] is True
        # Dev mode (no SMTP in tests) exposes the code so we can verify.
        code = body.get("dev_code")
        assert code and len(code) == 6

        # Login before verification is blocked with 403.
        early = client.post(
            "/api/v1/users/login",
            json={"login": email, "password": "secret123"},
        )
        assert early.status_code == 403

        bad = client.post(
            "/api/v1/users/verify-email",
            json={"email": email, "code": "000000"},
        )
        assert bad.status_code in (400, 401)

        ok = client.post(
            "/api/v1/users/verify-email",
            json={"email": email, "code": code},
        )
        assert ok.status_code == 200, ok.text
        assert ok.json()["token"]
        assert ok.json()["user"]["email_verified"] is True

        # Now normal login works.
        after = client.post(
            "/api/v1/users/login",
            json={"login": email, "password": "secret123"},
        )
        assert after.status_code == 200


class TestAuthConfig:
    def test_auth_config_public(self, client: TestClient) -> None:
        resp = client.get("/api/v1/users/auth-config")
        assert resp.status_code == 200
        data = resp.json()
        assert "google_client_id" in data
        assert "email_verification_enabled" in data


class TestHealthExposure:
    def test_public_health_hides_db_path_and_table_names(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("database") is None
        assert data.get("tables") == []
        assert data["table_count"] > 0
