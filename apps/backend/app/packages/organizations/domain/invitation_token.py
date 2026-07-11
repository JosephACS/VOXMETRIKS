"""Invitation token generation and verification (high-entropy secrets).

Plaintext token is returned once to the caller in academic mode.
Only SHA-256 hex digest is persisted. Never log plaintext tokens.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratedInvitationToken:
    """Plaintext is returned_once — never persist or audit this value."""

    plaintext: str
    token_hash: str
    returned_once: bool = True
    email_delivery_status: str = "not_sent"


def generate_invitation_token(*, nbytes: int = 32) -> GeneratedInvitationToken:
    plaintext = secrets.token_urlsafe(nbytes)
    return GeneratedInvitationToken(
        plaintext=plaintext,
        token_hash=hash_invitation_token(plaintext),
        returned_once=True,
        email_delivery_status="not_sent",
    )


def hash_invitation_token(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def verify_invitation_token(plaintext: str, token_hash: str) -> bool:
    digest = hash_invitation_token(plaintext)
    return hmac.compare_digest(digest, token_hash)
