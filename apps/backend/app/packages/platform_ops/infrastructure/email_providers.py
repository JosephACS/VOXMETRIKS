"""Email provider adapters — console (default), SMTP, Resend.

Never log secrets, codes, or API keys.
"""

from __future__ import annotations

import logging
import smtplib
import ssl
import uuid
from email.message import EmailMessage as StdEmailMessage
from typing import Optional
from urllib import error as urlerror
from urllib import request as urlrequest
import json

from app.core.config import get_settings
from app.packages.platform_ops.domain.ports import EmailMessage, EmailPort, EmailResult

logger = logging.getLogger("voxmetrik.email.providers")


def _sanitize_error(exc: BaseException) -> str:
    text = str(exc) or exc.__class__.__name__
    # Strip anything that looks like a credential
    lowered = text.lower()
    for needle in ("password", "api_key", "apikey", "authorization", "secret"):
        if needle in lowered:
            return f"{exc.__class__.__name__}: redacted"
    return text[:200]


class ConsoleEmailAdapter(EmailPort):
    """Default provider for tests/dev — logs metadata only, never sends."""

    code = "console"

    def send(self, message: EmailMessage) -> EmailResult:
        logger.info(
            "[CONSOLE EMAIL] provider=console template=%s to=%s subject=%s — NOT REAL EMAIL",
            message.template_code or "-",
            message.to_address,
            message.subject,
        )
        return EmailResult(
            success=True,
            provider_code=self.code,
            labeled_mock=True,
            message="[CONSOLE] Email logged — not a real delivery",
            provider_message_id=f"console_{uuid.uuid4().hex[:12]}",
        )


# Backward-compatible alias used by Spec 027 mock endpoint
class ConsoleMockEmailAdapter(ConsoleEmailAdapter):
    code = "console_mock_email"


class SmtpEmailAdapter(EmailPort):
    """Real SMTP delivery (Gmail app password supported)."""

    code = "smtp"

    def send(self, message: EmailMessage) -> EmailResult:
        cfg = get_settings()
        host = cfg.smtp_host.strip()
        user = (cfg.smtp_username or cfg.smtp_user or "").strip()
        password = cfg.smtp_password
        if not host or not user:
            return EmailResult(
                success=False,
                provider_code=self.code,
                labeled_mock=False,
                message="SMTP not configured",
                error_sanitized="smtp_not_configured",
            )

        from_addr = cfg.resolved_email_from_address
        from_name = cfg.resolved_email_from_name
        msg = StdEmailMessage()
        msg["Subject"] = message.subject
        msg["From"] = f"{from_name} <{from_addr}>" if from_name else from_addr
        msg["To"] = message.to_address
        text = message.body_text or message.body or ""
        msg.set_content(text)
        if message.body_html:
            msg.add_alternative(message.body_html, subtype="html")

        try:
            if cfg.smtp_use_tls:
                context = ssl.create_default_context()
                with smtplib.SMTP(host, cfg.smtp_port, timeout=15) as server:
                    server.starttls(context=context)
                    if password:
                        server.login(user, password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP_SSL(host, cfg.smtp_port, timeout=15) as server:
                    if password:
                        server.login(user, password)
                    server.send_message(msg)
            mid = f"smtp_{uuid.uuid4().hex[:12]}"
            logger.info(
                "[email] smtp sent template=%s to=%s message_id=%s",
                message.template_code or "-",
                message.to_address,
                mid,
            )
            return EmailResult(
                success=True,
                provider_code=self.code,
                labeled_mock=False,
                message="SMTP delivery accepted",
                provider_message_id=mid,
            )
        except Exception as exc:  # noqa: BLE001
            err = _sanitize_error(exc)
            logger.error("[email] smtp failed template=%s err=%s", message.template_code or "-", err)
            return EmailResult(
                success=False,
                provider_code=self.code,
                labeled_mock=False,
                message="SMTP delivery failed",
                error_sanitized=err,
            )


class ResendEmailAdapter(EmailPort):
    """Optional Resend HTTP API (no extra dependency)."""

    code = "resend"

    def send(self, message: EmailMessage) -> EmailResult:
        cfg = get_settings()
        api_key = (cfg.resend_api_key or "").strip()
        if not api_key:
            return EmailResult(
                success=False,
                provider_code=self.code,
                labeled_mock=False,
                message="Resend not configured",
                error_sanitized="resend_not_configured",
            )
        from_addr = (cfg.resend_from_address or cfg.resolved_email_from_address).strip()
        from_display = f"{cfg.resolved_email_from_name} <{from_addr}>"
        payload = {
            "from": from_display,
            "to": [message.to_address],
            "subject": message.subject,
            "text": message.body_text or message.body or "",
        }
        if message.body_html:
            payload["html"] = message.body_html
        data = json.dumps(payload).encode("utf-8")
        req = urlrequest.Request(
            "https://api.resend.com/emails",
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlrequest.urlopen(req, timeout=15) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            mid = None
            try:
                mid = json.loads(body).get("id")
            except Exception:
                mid = f"resend_{uuid.uuid4().hex[:12]}"
            logger.info(
                "[email] resend sent template=%s to=%s message_id=%s",
                message.template_code or "-",
                message.to_address,
                mid,
            )
            return EmailResult(
                success=True,
                provider_code=self.code,
                labeled_mock=False,
                message="Resend delivery accepted",
                provider_message_id=str(mid) if mid else None,
            )
        except urlerror.HTTPError as exc:
            err = _sanitize_error(exc)
            logger.error("[email] resend failed template=%s err=%s", message.template_code or "-", err)
            return EmailResult(
                success=False,
                provider_code=self.code,
                labeled_mock=False,
                message="Resend delivery failed",
                error_sanitized=err,
            )
        except Exception as exc:  # noqa: BLE001
            err = _sanitize_error(exc)
            logger.error("[email] resend failed template=%s err=%s", message.template_code or "-", err)
            return EmailResult(
                success=False,
                provider_code=self.code,
                labeled_mock=False,
                message="Resend delivery failed",
                error_sanitized=err,
            )


def get_email_adapter(code: Optional[str] = None) -> EmailPort:
    """Resolve provider from explicit code or EMAIL_PROVIDER setting.

    Pytest always uses console so tests never send real mail, even if
    the developer .env points at SMTP/Resend.
    """
    cfg = get_settings()
    if code is None and cfg.is_test_runtime:
        return ConsoleEmailAdapter()
    raw = (code or cfg.email_provider or "console").strip().lower()
    if raw in {"console", "console_mock_email", "mock", ""}:
        return ConsoleEmailAdapter() if raw != "console_mock_email" else ConsoleMockEmailAdapter()
    if raw == "smtp":
        return SmtpEmailAdapter()
    if raw == "resend":
        return ResendEmailAdapter()
    raise ValueError(f"Unknown email adapter: {raw}")


def get_configured_email_port() -> EmailPort:
    return get_email_adapter()
