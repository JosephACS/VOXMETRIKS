"""Platform ops infrastructure adapters — Spec 027.

Email providers live in email_providers.py (console | smtp | resend).
This module keeps notification adapters and re-exports email helpers.
"""

from __future__ import annotations

import logging

from app.packages.platform_ops.domain.ports import (
    NotificationMessage,
    NotificationPort,
    NotificationResult,
)
from app.packages.platform_ops.infrastructure.email_providers import (
    ConsoleMockEmailAdapter,
    ConsoleEmailAdapter,
    ResendEmailAdapter,
    SmtpEmailAdapter,
    get_email_adapter,
    get_configured_email_port,
)

logger = logging.getLogger("voxmetrik.platform_ops.adapters")

__all__ = [
    "ConsoleNotificationAdapter",
    "ConsoleMockEmailAdapter",
    "ConsoleEmailAdapter",
    "SmtpEmailAdapter",
    "ResendEmailAdapter",
    "get_notification_adapter",
    "get_email_adapter",
    "get_configured_email_port",
]


class ConsoleNotificationAdapter(NotificationPort):
    """Writes notifications to structured logs — not a real delivery channel."""

    code = "console"

    def send(self, message: NotificationMessage) -> NotificationResult:
        logger.info(
            "[CONSOLE NOTIFICATION] to=%s subject=%s body=%s",
            message.recipient, message.subject, message.body[:200],
        )
        return NotificationResult(
            success=True,
            adapter_code=self.code,
            labeled_mock=True,
            message="[CONSOLE] Notification logged — not a real delivery channel",
        )


def get_notification_adapter(code: str = "console") -> NotificationPort:
    if code == "console":
        return ConsoleNotificationAdapter()
    raise ValueError(f"Unknown notification adapter: {code}")
