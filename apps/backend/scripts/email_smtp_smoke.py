#!/usr/bin/env python3
"""Optional real SMTP/Resend smoke. Never runs during pytest.

Sends exactly ONE email, and only when invoked with ``--send``.

Exit codes:
  0 = sent OK
  2 = NOT_CONFIGURED / NOT_RUN (missing flag, credentials, or EMAIL_SMOKE_TEST_TO)
  1 = send failed
"""

from __future__ import annotations

import os
import sys

# Ensure backend package root is importable when run as a script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import get_settings
from app.packages.platform_ops.application.email_templates import verification_code_email
from app.packages.platform_ops.domain.ports import EmailMessage
from app.packages.platform_ops.infrastructure.email_providers import get_email_adapter


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--send" not in args:
        print("NOT_RUN: pass --send to send exactly one smoke email (no send performed)")
        return 2

    get_settings.cache_clear()
    cfg = get_settings()
    to_addr = (cfg.email_smoke_test_to or os.environ.get("EMAIL_SMOKE_TEST_TO", "")).strip()
    provider = (cfg.email_provider or "console").strip().lower()

    if provider in {"console", "mock", "console_mock_email", ""}:
        print("NOT_CONFIGURED: EMAIL_PROVIDER is console (no real send)")
        return 2
    if not to_addr:
        print("NOT_CONFIGURED: set EMAIL_SMOKE_TEST_TO")
        return 2
    if provider == "smtp" and not cfg.email_enabled:
        print("NOT_CONFIGURED: SMTP_HOST / SMTP_USERNAME missing")
        return 2
    if provider == "resend" and not (cfg.resend_api_key or "").strip():
        print("NOT_CONFIGURED: RESEND_API_KEY missing")
        return 2

    # Explicit adapter — never fall through to pytest console guard accidentally
    rendered = verification_code_email(to_name="Smoke", code="000000", expires_min=5)
    port = get_email_adapter(provider)
    result = port.send(
        EmailMessage(
            to_address=to_addr,
            subject=f"[SMOKE] {rendered.subject}",
            body_text=rendered.body_text + "\n\n(This is an SMTP smoke test; code is invalid.)",
            body_html=rendered.body_html,
            template_code="smoke.verification",
        )
    )
    if result.success and not result.labeled_mock:
        print(f"PASS: real email sent via {result.provider_code} id={result.provider_message_id}")
        return 0
    if result.labeled_mock:
        print("NOT_CONFIGURED: provider returned console/mock")
        return 2
    print(f"FAIL: {result.error_sanitized or result.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
