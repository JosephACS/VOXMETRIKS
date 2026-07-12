"""Transactional email ports — Spec 027 (real + console providers)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class NotificationMessage:
    recipient: str
    subject: str
    body: str
    channel: str = "console"


@dataclass(frozen=True)
class NotificationResult:
    success: bool
    adapter_code: str
    labeled_mock: bool
    message: str


class NotificationPort(ABC):
    @abstractmethod
    def send(self, message: NotificationMessage) -> NotificationResult:
        ...


@dataclass(frozen=True)
class EmailMessage:
    to_address: str
    subject: str
    body_text: str
    body_html: Optional[str] = None
    template_code: Optional[str] = None
    organization_id: Optional[int] = None
    related_type: Optional[str] = None
    related_id: Optional[str] = None

    @property
    def body(self) -> str:
        """Legacy alias for Spec 027 mock callers."""
        return self.body_text


@dataclass(frozen=True)
class EmailResult:
    success: bool
    provider_code: str
    labeled_mock: bool
    message: str
    provider_message_id: Optional[str] = None
    error_sanitized: Optional[str] = None


class EmailPort(ABC):
    """Configurable email delivery (console | smtp | resend)."""

    code: str

    @abstractmethod
    def send(self, message: EmailMessage) -> EmailResult:
        ...
