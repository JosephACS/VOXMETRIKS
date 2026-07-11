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
