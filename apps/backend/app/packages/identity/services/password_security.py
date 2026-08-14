"""Password hashing — bcrypt with transparent SHA-256 legacy support."""

from __future__ import annotations

import hashlib
import re

import bcrypt

_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _legacy_sha256(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def is_legacy_hash(stored_hash: str) -> bool:
    return bool(_SHA256_HEX.match(stored_hash or ""))


def verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash:
        return False
    if stored_hash.startswith("$2"):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
        except ValueError:
            return False
    if is_legacy_hash(stored_hash):
        return _legacy_sha256(password) == stored_hash.lower()
    return False


def needs_rehash(stored_hash: str) -> bool:
    return is_legacy_hash(stored_hash)


# Shared account-password policy (register / reset / change). PIN is separate.
MIN_ACCOUNT_PASSWORD_LENGTH = 8
MAX_ACCOUNT_PASSWORD_LENGTH = 128
COMMON_ACCOUNT_PASSWORDS = frozenset(
    {
        "password",
        "123456",
        "1234",
        "12345678",
        "qwerty",
        "letmein",
        "admin",
        "passw0rd",
        "demo123",
        "admin123",
    }
)


class PasswordPolicyError(ValueError):
    """Account password rejected by the shared policy."""

    def __init__(self, message: str, *, code: str = "password_weak") -> None:
        super().__init__(message)
        self.code = code


def validate_account_password(
    password: str,
    *,
    current_password: str | None = None,
) -> str:
    """Return the password if it satisfies the shared account policy."""
    value = password or ""
    if len(value) < MIN_ACCOUNT_PASSWORD_LENGTH:
        raise PasswordPolicyError("password must be at least 8 characters")
    if len(value) > MAX_ACCOUNT_PASSWORD_LENGTH:
        raise PasswordPolicyError("password must be at most 128 characters")
    if current_password is not None and value == current_password:
        raise PasswordPolicyError(
            "password must be different from current",
            code="password_same",
        )
    if value.lower() in COMMON_ACCOUNT_PASSWORDS:
        raise PasswordPolicyError("choose a stronger password")
    return value
