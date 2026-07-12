"""Platform ops ports — Spec 027."""

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
    body: str


@dataclass(frozen=True)
class EmailResult:
    success: bool
    labeled_mock: bool
    message: str


class EmailPort(ABC):
    @abstractmethod
    def send(self, message: EmailMessage) -> EmailResult:
        ...
