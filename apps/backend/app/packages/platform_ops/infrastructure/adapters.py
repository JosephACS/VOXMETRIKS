"""Platform ops infrastructure adapters — Spec 027."""

from __future__ import annotations

import logging

from app.packages.platform_ops.domain.ports import (
    EmailMessage,
    EmailPort,
    EmailResult,
    NotificationMessage,
    NotificationPort,
    NotificationResult,
)

logger = logging.getLogger("voxmetrik.platform_ops.adapters")


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


class ConsoleMockEmailAdapter(EmailPort):
    """MOCK email adapter — explicitly labeled, not real email."""

    code = "console_mock_email"

    def send(self, message: EmailMessage) -> EmailResult:
        logger.info(
            "[MOCK EMAIL] to=%s subject=%s — NOT REAL EMAIL",
            message.to_address, message.subject,
        )
        return EmailResult(
            success=True,
            labeled_mock=True,
            message="[MOCK] Email logged to console — not a real email service",
        )


def get_notification_adapter(code: str = "console") -> NotificationPort:
    if code == "console":
        return ConsoleNotificationAdapter()
    raise ValueError(f"Unknown notification adapter: {code}")


def get_email_adapter(code: str = "console_mock_email") -> EmailPort:
    if code == "console_mock_email":
        return ConsoleMockEmailAdapter()
    raise ValueError(f"Unknown email adapter: {code}")
