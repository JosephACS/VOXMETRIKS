"""Payment provider abstractions — Spec 019 / 027.

Academic mock is explicitly labeled; never presented as a real gateway.
No PAN/CVV accepted or stored. Demo scenarios only outside production.
"""

from __future__ import annotations

import hashlib
import hmac
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional

from app.core.config import get_settings
from app.core.time_util import utc_now


MOCK_SCENARIOS = frozenset(
    {
        "succeeded",
        "declined",
        "insufficient_funds",
        "invalid_method",
        "timeout",
        "processing",
        "canceled",
        "duplicate_event",
        "partial_payment",
        "full_refund",
        "partial_refund",
        "reversal",
    }
)


@dataclass(frozen=True)
class ProviderChargeRequest:
    amount: Decimal
    currency: str
    idempotency_key: str
    invoice_id: int
    organization_id: int
    # Tokenized / reference only — never raw card data
    payment_method_token: Optional[str] = None
    # Demo-only outcome selector (ignored / rejected in production)
    scenario: Optional[str] = None
    payment_attempt_id: Optional[int] = None


@dataclass(frozen=True)
class ProviderChargeResult:
    success: bool
    provider_attempt_id: str
    labeled_mock: bool
    message: str
    status: str = "succeeded"
    error_code: Optional[str] = None
    provider_event_id: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    scenario: Optional[str] = None


@dataclass(frozen=True)
class SimulatedProviderEvent:
    provider_event_id: str
    idempotency_key: str
    amount: Decimal
    currency: str
    payment_attempt_id: Optional[int]
    timestamp: str
    status: str
    error_code: Optional[str]
    event_type: str
    labeled_mock: bool = True


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
    """Simulated academic provider — always labeled [MOCK]. Alias of MockPaymentProvider."""

    code = "academic_mock"
    is_mock = True

    def charge(self, request: ProviderChargeRequest) -> ProviderChargeResult:
        return MockPaymentProvider().charge(request)

    def simulate(
        self, request: ProviderChargeRequest, scenario: str
    ) -> tuple[ProviderChargeResult, SimulatedProviderEvent]:
        return MockPaymentProvider().simulate(request, scenario)


class MockPaymentProvider(PaymentProvider):
    """Configurable demo payment simulator — never moves real money."""

    code = "academic_mock"
    is_mock = True

    def charge(self, request: ProviderChargeRequest) -> ProviderChargeResult:
        scenario = (request.scenario or "succeeded").strip().lower()
        result, _ = self.simulate(request, scenario)
        return result

    def simulate(
        self, request: ProviderChargeRequest, scenario: str
    ) -> tuple[ProviderChargeResult, SimulatedProviderEvent]:
        cfg = get_settings()
        if cfg.is_production:
            raise PermissionError("Mock payment scenarios are disabled in production")
        scenario_n = (scenario or "succeeded").strip().lower()
        if scenario_n not in MOCK_SCENARIOS:
            raise ValueError(f"Unknown mock scenario={scenario_n!r}")

        token = f"mock_{hashlib.sha256(request.idempotency_key.encode()).hexdigest()[:12]}"
        event_id = f"evt_{uuid.uuid4().hex[:16]}"
        amount = request.amount
        status = "succeeded"
        success = True
        error_code: Optional[str] = None
        event_type = "payment.succeeded"

        if scenario_n == "succeeded":
            status, success, event_type = "succeeded", True, "payment.succeeded"
        elif scenario_n == "declined":
            status, success, error_code, event_type = (
                "failed", False, "card_declined", "payment.failed",
            )
        elif scenario_n == "insufficient_funds":
            status, success, error_code, event_type = (
                "failed", False, "insufficient_funds", "payment.failed",
            )
        elif scenario_n == "invalid_method":
            status, success, error_code, event_type = (
                "failed", False, "invalid_method", "payment.failed",
            )
        elif scenario_n == "timeout":
            status, success, error_code, event_type = (
                "failed", False, "provider_timeout", "payment.failed",
            )
        elif scenario_n == "processing":
            status, success, event_type = "processing", True, "payment.processing"
        elif scenario_n == "canceled":
            status, success, error_code, event_type = (
                "canceled", False, "canceled_by_user", "payment.canceled",
            )
        elif scenario_n == "duplicate_event":
            # Same deterministic event id derived from idempotency key
            event_id = f"evt_dup_{hashlib.sha256(request.idempotency_key.encode()).hexdigest()[:16]}"
            status, success, event_type = "succeeded", True, "payment.succeeded"
        elif scenario_n == "partial_payment":
            amount = (request.amount / Decimal("2")).quantize(Decimal("0.0001"))
            status, success, event_type = "succeeded", True, "payment.partial"
        elif scenario_n == "full_refund":
            status, success, event_type = "refunded", True, "payment.refunded"
        elif scenario_n == "partial_refund":
            amount = (request.amount / Decimal("2")).quantize(Decimal("0.0001"))
            status, success, event_type = "partially_refunded", True, "payment.partial_refund"
        elif scenario_n == "reversal":
            status, success, event_type = "reversed", True, "payment.reversed"

        result = ProviderChargeResult(
            success=success,
            provider_attempt_id=token,
            labeled_mock=True,
            message=f"[MOCK] Simulated scenario={scenario_n} — not a real payment",
            status=status,
            error_code=error_code,
            provider_event_id=event_id,
            amount=amount,
            currency=request.currency,
            scenario=scenario_n,
        )
        event = SimulatedProviderEvent(
            provider_event_id=event_id,
            idempotency_key=request.idempotency_key,
            amount=amount,
            currency=request.currency,
            payment_attempt_id=request.payment_attempt_id,
            timestamp=utc_now().isoformat(),
            status=status,
            error_code=error_code,
            event_type=event_type,
            labeled_mock=True,
        )
        return result, event


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
            status="succeeded",
        )


def get_provider(code: str) -> PaymentProvider:
    if code in {AcademicMockProvider.code, "mock", "mock_payment"}:
        return MockPaymentProvider()
    if code == ManualTransferRecorder.code:
        return ManualTransferRecorder()
    raise ValueError(f"Unknown payment provider code={code!r}")


def event_payload_dict(event: SimulatedProviderEvent) -> dict[str, Any]:
    return {
        "provider_event_id": event.provider_event_id,
        "idempotency_key": event.idempotency_key,
        "amount": str(event.amount),
        "currency": event.currency,
        "payment_attempt_id": event.payment_attempt_id,
        "timestamp": event.timestamp,
        "status": event.status,
        "error_code": event.error_code,
        "event_type": event.event_type,
        "labeled_mock": True,
    }
