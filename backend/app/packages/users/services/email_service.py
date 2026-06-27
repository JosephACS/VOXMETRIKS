"""Email delivery for account verification codes.

Uses the stdlib ``smtplib`` (no extra dependency). When SMTP is not configured
(``settings.email_enabled`` is False) the service runs in *dev mode*: it does
not send anything and signals the caller to surface the code locally so the
flow can be tested on localhost without a real mailbox.
"""

from __future__ import annotations

import logging
import secrets
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def generate_code(length: int = 6) -> str:
    """Cryptographically-strong numeric code (zero-padded)."""
    upper = 10 ** length
    return str(secrets.randbelow(upper)).zfill(length)


def _build_message(to_email: str, code: str) -> EmailMessage:
    cfg = get_settings()
    brand = cfg.app_public_name
    msg = EmailMessage()
    msg["Subject"] = f"{brand} · Tu código de verificación: {code}"
    msg["From"] = cfg.email_from_address
    msg["To"] = to_email
    msg.set_content(
        f"Bienvenido a {brand}.\n\n"
        f"Tu código de verificación es: {code}\n\n"
        f"Expira en {cfg.email_code_ttl_min} minutos. "
        f"Si no creaste esta cuenta, ignora este correo.\n"
    )
    msg.add_alternative(
        f"""
        <div style="font-family:system-ui,Segoe UI,Roboto,sans-serif;max-width:420px;margin:auto">
          <h2 style="margin:0 0 8px">{brand}</h2>
          <p style="color:#555">Tu código de verificación:</p>
          <p style="font-size:32px;font-weight:700;letter-spacing:6px;margin:8px 0">{code}</p>
          <p style="color:#888;font-size:13px">Expira en {cfg.email_code_ttl_min} minutos.
          Si no creaste esta cuenta, ignora este correo.</p>
        </div>
        """,
        subtype="html",
    )
    return msg


def send_verification_email(to_email: str, code: str) -> bool:
    """Send the code via SMTP. Returns True if sent, False in dev mode/failure.

    In dev mode (no SMTP configured) the code is logged so it can be used on
    localhost; the route also returns it to the client in that case.
    """
    cfg = get_settings()
    if not cfg.email_enabled:
        logger.warning(
            "[email] SMTP not configured — DEV MODE. Verification code for %s: %s",
            to_email, code,
        )
        return False

    msg = _build_message(to_email, code)
    try:
        if cfg.smtp_use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=10) as server:
                server.starttls(context=context)
                server.login(cfg.smtp_user, cfg.smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP_SSL(cfg.smtp_host, cfg.smtp_port, timeout=10) as server:
                server.login(cfg.smtp_user, cfg.smtp_password)
                server.send_message(msg)
        logger.info("[email] verification code sent to %s", to_email)
        return True
    except Exception as exc:  # noqa: BLE001 — never leak SMTP errors to the user
        logger.error("[email] failed to send verification code to %s: %s", to_email, exc)
        return False
