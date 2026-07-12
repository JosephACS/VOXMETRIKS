"""Email delivery for account verification / transactional mail.

Delegates to Spec 027 EmailPort (console | smtp | resend).
Never logs plaintext codes or SMTP credentials.
"""

from __future__ import annotations

import logging
import secrets
from typing import Any, Optional

import duckdb

from app.core.config import get_settings
from app.packages.platform_ops.application.email_service import send_rendered_email
from app.packages.platform_ops.application.email_templates import verification_code_email

logger = logging.getLogger(__name__)


def generate_code(length: int = 6) -> str:
    """Cryptographically-strong numeric code (zero-padded)."""
    upper = 10 ** length
    return str(secrets.randbelow(upper)).zfill(length)


def send_verification_email(
    to_email: str,
    code: str,
    *,
    conn: Optional[duckdb.DuckDBPyConnection] = None,
    to_name: Optional[str] = None,
    locale: Optional[str] = None,
) -> dict[str, Any]:
    """Send verification code. Returns delivery metadata (never includes code)."""
    cfg = get_settings()
    rendered = verification_code_email(
        to_name=to_name,
        code=code,
        expires_min=cfg.email_code_ttl_min,
        locale=locale or "es",
    )
    result = send_rendered_email(
        to_address=to_email,
        rendered=rendered,
        conn=conn,
        related_type="auth_verification",
        related_id=to_email.lower(),
    )
    return {
        "email_sent": bool(result.success),
        "provider": result.provider_code,
        "console": bool(result.labeled_mock),
        "success": result.success,
        "provider_message_id": result.provider_message_id,
    }
