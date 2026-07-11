"""Verify Google Sign-In ID tokens.

Uses Google's public ``tokeninfo`` endpoint (no extra dependency; httpx is
already required). Suitable for low-volume / academic use. The endpoint
validates the token signature and expiry server-side; we additionally check
the audience matches our configured client id and the issuer is Google.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
_VALID_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


def verify_google_id_token(credential: str) -> Optional[Dict[str, Any]]:
    """Return verified claims ``{email, name, sub, email_verified}`` or None."""
    cfg = get_settings()
    client_id = cfg.google_client_id.strip()
    if not client_id:
        logger.warning("[google] GOOGLE_CLIENT_ID not configured")
        return None
    if not credential:
        return None

    try:
        resp = httpx.get(_TOKENINFO_URL, params={"id_token": credential}, timeout=8.0)
    except httpx.HTTPError as exc:
        logger.error("[google] tokeninfo request failed: %s", exc)
        return None

    if resp.status_code != 200:
        logger.warning("[google] tokeninfo rejected token (%s)", resp.status_code)
        return None

    claims = resp.json()
    if claims.get("aud") != client_id:
        logger.warning("[google] audience mismatch")
        return None
    if claims.get("iss") not in _VALID_ISSUERS:
        logger.warning("[google] invalid issuer: %s", claims.get("iss"))
        return None

    email = (claims.get("email") or "").strip().lower()
    if not email:
        return None

    return {
        "email": email,
        "name": (claims.get("name") or "").strip(),
        "sub": claims.get("sub"),
        "email_verified": str(claims.get("email_verified", "false")).lower() == "true",
    }
