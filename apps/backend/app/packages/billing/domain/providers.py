"""Payment provider abstractions — Spec 019.

Academic mock is explicitly labeled; never presented as a real gateway.
No PAN/CVV accepted or stored.
"""

from __future__ import annotations

import hashlib
import hmac
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class ProviderChargeRequest:
    amount: Decimal
    currency: str
    idempotency_key: str
    invoice_id: int
    organization_id: int
    # Tokenized / reference only — never raw card data
    payment_method_token: Optional[str] = None


@dataclass(frozen=True)
class ProviderChargeResult:
    success: bool
    provider_attempt_id: str
    labeled_mock: bool
    message: str


class PaymentProvider(ABC):
    """Interface for payment providers (academic / manual / future real)."""

    code: str
    is_mock: bool

    @abstractmethod
    def charge(self, request: ProviderChargeRequest) -> ProviderChargeResult:
        ...

    def verify_webhook_signature(
        self,
        *,
        payload: bytes,
        signature_header: str,
        secret: str,
    ) -> bool:
        """Conceptual HMAC signature check for provider webhooks."""
        expected = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature_header.strip())


class AcademicMockProvider(PaymentProvider):
    """Simulated academic provider — always labeled [MOCK]."""

    code = "academic_mock"
    is_mock = True

    def charge(self, request: ProviderChargeRequest) -> ProviderChargeResult:
        token = f"mock_{hashlib.sha256(request.idempotency_key.encode()).hexdigest()[:12]}"
        return ProviderChargeResult(
            success=True,
            provider_attempt_id=token,
            labeled_mock=True,
            message="[MOCK] Academic mock charge recorded — not a real payment gateway",
        )


class ManualTransferRecorder(PaymentProvider):
    """Records a manual / bank-transfer payment reference — not mock, not card."""

    code = "manual_transfer"
    is_mock = False

    def charge(self, request: ProviderChargeRequest) -> ProviderChargeResult:
        ref = request.payment_method_token or request.idempotency_key
        token = f"xfer_{hashlib.sha256(ref.encode()).hexdigest()[:12]}"
        return ProviderChargeResult(
            success=True,
            provider_attempt_id=token,
            labeled_mock=False,
            message="Manual transfer recorded for later reconciliation",
        )


def get_provider(code: str) -> PaymentProvider:
    if code == AcademicMockProvider.code:
        return AcademicMockProvider()
    if code == ManualTransferRecorder.code:
        return ManualTransferRecorder()
    raise ValueError(f"Unknown payment provider code={code!r}")
