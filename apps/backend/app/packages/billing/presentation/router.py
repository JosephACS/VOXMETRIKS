"""Billing HTTP router — Spec 019.

All endpoints under /billing prefix.
Mounted at /api/v1/billing in main.py.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

import duckdb
from fastapi import APIRouter, Depends, Query, Response

from app.packages.billing.application.use_cases import (
    BillingProfileUseCases,
    CreditNoteUseCases,
    InvoiceUseCases,
    LedgerUseCases,
    PaymentAttemptUseCases,
    PaymentMethodUseCases,
    PaymentUseCases,
    ProviderEventUseCases,
    RefundUseCases,
)
from app.packages.billing.domain.errors import BillingError
from app.packages.billing.presentation.dependencies import (
    get_authenticated_billing_user,
    require_org_billing_permission,
)
from app.packages.billing.presentation.error_mapping import raise_billing_http
from app.packages.billing.presentation.schemas import (
    BillingProfileCreateRequest,
    BillingProfileOut,
    BillingProfileUpdateRequest,
    CreditNoteCreateRequest,
    CreditNoteOut,
    InvoiceCreateRequest,
    InvoiceItemAddRequest,
    InvoiceItemOut,
    InvoiceOut,
    InvoiceVoidRequest,
    LedgerEntryOut,
    ManualTransferRequest,
    PaginatedAttempts,
    PaginatedCreditNotes,
    PaginatedInvoices,
    PaginatedLedger,
    PaginatedPayments,
    PaginatedRefunds,
    PaymentAllocationOut,
    PaymentAllocateRequest,
    PaymentAttemptCreateRequest,
    PaymentAttemptOut,
    PaymentAttemptRetryRequest,
    PaymentMethodCreateRequest,
    PaymentMethodOut,
    PaymentOut,
    PaymentReverseRequest,
    ProviderEventOut,
    ProviderEventRequest,
    RefundCreateRequest,
    RefundOut,
)

billing_router = APIRouter(prefix="/billing", tags=["Billing"])


def _page(page: int, page_size: int, max_size: int = 100) -> tuple[int, int, int]:
    page = max(1, page)
    ps = min(max(1, page_size), max_size)
    return page, ps, (page - 1) * ps


def _attempt_out(a) -> PaymentAttemptOut:
    return PaymentAttemptOut(
        id=a.id, organization_id=a.organization_id, invoice_id=a.invoice_id,
        payment_method_ref_id=a.payment_method_ref_id,
        provider_code=a.provider_code, idempotency_key=a.idempotency_key,
        amount=a.amount, currency=a.currency, status=a.status,
        provider_attempt_id=a.provider_attempt_id,
        failure_reason=a.failure_reason,
        is_mock=(a.provider_code == "academic_mock"),
        created_at=a.created_at, updated_at=a.updated_at,
    )


# ── Billing Profile ────────────────────────────────────────────────────────────

@billing_router.get("/profile", response_model=BillingProfileOut)
def get_billing_profile(
    ctx: dict = Depends(get_authenticated_billing_user),
) -> BillingProfileOut:
    try:
        profile = BillingProfileUseCases(ctx["conn"]).get_by_org(ctx["organization_id"])
    except BillingError as e:
        raise_billing_http(e)
    return BillingProfileOut(**profile.__dict__)


@billing_router.post("/profile", response_model=BillingProfileOut, status_code=201)
def create_billing_profile(
    body: BillingProfileCreateRequest,
    ctx: dict = Depends(require_org_billing_permission("billing.manage")),
) -> BillingProfileOut:
    try:
        profile = BillingProfileUseCases(ctx["conn"]).create(
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            default_currency=body.default_currency,
            legal_name=body.legal_name,
            tax_id=body.tax_id,
            billing_address=body.billing_address,
            email=body.email,
            request_id=ctx["request_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return BillingProfileOut(**profile.__dict__)


@billing_router.patch("/profile", response_model=BillingProfileOut)
def update_billing_profile(
    body: BillingProfileUpdateRequest,
    ctx: dict = Depends(require_org_billing_permission("billing.manage")),
) -> BillingProfileOut:
    try:
        profile = BillingProfileUseCases(ctx["conn"]).update(
            ctx["organization_id"],
            actor_user_id=ctx["user_id"],
            legal_name=body.legal_name,
            tax_id=body.tax_id,
            billing_address=body.billing_address,
            email=body.email,
            request_id=ctx["request_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return BillingProfileOut(**profile.__dict__)


# ── Invoices ───────────────────────────────────────────────────────────────────

@billing_router.get("/invoices", response_model=PaginatedInvoices)
def list_invoices(
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_org_billing_permission("invoice.view")),
) -> PaginatedInvoices:
    p, ps, offset = _page(page, page_size)
    items, total = InvoiceUseCases(ctx["conn"]).list(
        organization_id=ctx["organization_id"], status=status,
        limit=ps, offset=offset,
    )
    return PaginatedInvoices(
        items=[InvoiceOut(**i.__dict__) for i in items],
        total=total, page=p, page_size=ps,
    )


@billing_router.post("/invoices", response_model=InvoiceOut, status_code=201)
def create_invoice(
    body: InvoiceCreateRequest,
    ctx: dict = Depends(require_org_billing_permission("invoice.create")),
) -> InvoiceOut:
    try:
        inv = InvoiceUseCases(ctx["conn"]).create(
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            billing_profile_id=body.billing_profile_id,
            subscription_id=body.subscription_id,
            period_start=body.period_start,
            period_end=body.period_end,
            due_date=body.due_date,
            notes=body.notes,
            request_id=ctx["request_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return InvoiceOut(**inv.__dict__)


@billing_router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: int,
    ctx: dict = Depends(require_org_billing_permission("invoice.view")),
) -> InvoiceOut:
    try:
        inv = InvoiceUseCases(ctx["conn"]).get(invoice_id, organization_id=ctx["organization_id"])
    except BillingError as e:
        raise_billing_http(e)
    return InvoiceOut(**inv.__dict__)


@billing_router.post("/invoices/{invoice_id}/items", response_model=InvoiceItemOut, status_code=201)
def add_invoice_item(
    invoice_id: int,
    body: InvoiceItemAddRequest,
    ctx: dict = Depends(require_org_billing_permission("invoice.create")),
) -> InvoiceItemOut:
    try:
        item = InvoiceUseCases(ctx["conn"]).add_item(
            invoice_id,
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            description=body.description,
            quantity=body.quantity,
            unit_price=body.unit_price,
            period_start=body.period_start,
            period_end=body.period_end,
        )
    except BillingError as e:
        raise_billing_http(e)
    return InvoiceItemOut(**item.__dict__)


@billing_router.get("/invoices/{invoice_id}/items", response_model=list[InvoiceItemOut])
def list_invoice_items(
    invoice_id: int,
    ctx: dict = Depends(require_org_billing_permission("invoice.view")),
) -> list[InvoiceItemOut]:
    items = InvoiceUseCases(ctx["conn"]).list_items(invoice_id)
    return [InvoiceItemOut(**i.__dict__) for i in items]


@billing_router.post("/invoices/{invoice_id}/issue", response_model=InvoiceOut)
def issue_invoice(
    invoice_id: int,
    ctx: dict = Depends(require_org_billing_permission("invoice.create")),
) -> InvoiceOut:
    try:
        inv = InvoiceUseCases(ctx["conn"]).issue(
            invoice_id,
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            request_id=ctx["request_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return InvoiceOut(**inv.__dict__)


@billing_router.post("/invoices/{invoice_id}/void", response_model=InvoiceOut)
def void_invoice(
    invoice_id: int,
    body: InvoiceVoidRequest,
    ctx: dict = Depends(require_org_billing_permission("invoice.void")),
) -> InvoiceOut:
    try:
        inv = InvoiceUseCases(ctx["conn"]).void(
            invoice_id,
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            reason=body.reason,
            request_id=ctx["request_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return InvoiceOut(**inv.__dict__)


@billing_router.post("/invoices/{invoice_id}/mark-past-due", response_model=InvoiceOut)
def mark_invoice_past_due(
    invoice_id: int,
    ctx: dict = Depends(require_org_billing_permission("billing.manage")),
) -> InvoiceOut:
    try:
        inv = InvoiceUseCases(ctx["conn"]).mark_past_due(
            invoice_id,
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            request_id=ctx["request_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return InvoiceOut(**inv.__dict__)


# ── Payment Methods ────────────────────────────────────────────────────────────

@billing_router.get("/payment-methods", response_model=list[PaymentMethodOut])
def list_payment_methods(
    ctx: dict = Depends(require_org_billing_permission("billing.view")),
) -> list[PaymentMethodOut]:
    methods = PaymentMethodUseCases(ctx["conn"]).list(ctx["organization_id"])
    return [
        PaymentMethodOut(
            id=m.id, organization_id=m.organization_id, provider_code=m.provider_code,
            display_label=m.display_label, method_type=m.method_type,
            is_default=m.is_default, status=m.status,
            created_at=m.created_at, updated_at=m.updated_at,
        )
        for m in methods
    ]


@billing_router.post("/payment-methods", response_model=PaymentMethodOut, status_code=201)
def create_payment_method(
    body: PaymentMethodCreateRequest,
    ctx: dict = Depends(require_org_billing_permission("billing.manage")),
) -> PaymentMethodOut:
    try:
        m = PaymentMethodUseCases(ctx["conn"]).create(
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            provider_code=body.provider_code,
            display_label=body.display_label,
            token_ref=body.token_ref,
            method_type=body.method_type,
            is_default=body.is_default,
        )
    except BillingError as e:
        raise_billing_http(e)
    return PaymentMethodOut(
        id=m.id, organization_id=m.organization_id, provider_code=m.provider_code,
        display_label=m.display_label, method_type=m.method_type,
        is_default=m.is_default, status=m.status,
        created_at=m.created_at, updated_at=m.updated_at,
    )


@billing_router.delete("/payment-methods/{method_id}", status_code=204, response_model=None)
def remove_payment_method(
    method_id: int,
    ctx: dict = Depends(require_org_billing_permission("billing.manage")),
) -> Response:
    try:
        PaymentMethodUseCases(ctx["conn"]).remove(
            method_id, organization_id=ctx["organization_id"],
            actor_user_id=ctx["user_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return Response(status_code=204)


# ── Payment Attempts ───────────────────────────────────────────────────────────

@billing_router.get("/payment-attempts", response_model=PaginatedAttempts)
def list_payment_attempts(
    invoice_id: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_org_billing_permission("payment.view")),
) -> PaginatedAttempts:
    p, ps, offset = _page(page, page_size)
    items, total = PaymentAttemptUseCases(ctx["conn"]).list(
        organization_id=ctx["organization_id"], invoice_id=invoice_id,
        limit=ps, offset=offset,
    )
    return PaginatedAttempts(
        items=[_attempt_out(a) for a in items],
        total=total, page=p, page_size=ps,
    )


@billing_router.post("/payment-attempts", response_model=PaymentAttemptOut, status_code=201)
def create_payment_attempt(
    body: PaymentAttemptCreateRequest,
    ctx: dict = Depends(require_org_billing_permission("payment.manage")),
) -> PaymentAttemptOut:
    try:
        attempt = PaymentAttemptUseCases(ctx["conn"]).create(
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            invoice_id=body.invoice_id,
            provider_code=body.provider_code,
            idempotency_key=body.idempotency_key,
            amount=body.amount,
            currency=body.currency,
            payment_method_ref_id=body.payment_method_ref_id,
            request_id=ctx["request_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return _attempt_out(attempt)


@billing_router.get("/payment-attempts/{attempt_id}", response_model=PaymentAttemptOut)
def get_payment_attempt(
    attempt_id: int,
    ctx: dict = Depends(require_org_billing_permission("payment.view")),
) -> PaymentAttemptOut:
    try:
        attempt = PaymentAttemptUseCases(ctx["conn"]).get(
            attempt_id, organization_id=ctx["organization_id"]
        )
    except BillingError as e:
        raise_billing_http(e)
    return _attempt_out(attempt)


@billing_router.post("/payment-attempts/{attempt_id}/confirm", response_model=PaymentAttemptOut)
def confirm_mock_attempt(
    attempt_id: int,
    ctx: dict = Depends(require_org_billing_permission("payment.manage")),
) -> PaymentAttemptOut:
    try:
        attempt = PaymentAttemptUseCases(ctx["conn"]).confirm_mock(
            attempt_id,
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            request_id=ctx["request_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return _attempt_out(attempt)


@billing_router.post("/payment-attempts/{attempt_id}/cancel", response_model=PaymentAttemptOut)
def cancel_payment_attempt(
    attempt_id: int,
    ctx: dict = Depends(require_org_billing_permission("payment.manage")),
) -> PaymentAttemptOut:
    try:
        attempt = PaymentAttemptUseCases(ctx["conn"]).cancel(
            attempt_id,
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return _attempt_out(attempt)


@billing_router.post("/payment-attempts/{attempt_id}/retry", response_model=PaymentAttemptOut, status_code=201)
def retry_payment_attempt(
    attempt_id: int,
    body: PaymentAttemptRetryRequest,
    ctx: dict = Depends(require_org_billing_permission("payment.manage")),
) -> PaymentAttemptOut:
    try:
        attempt = PaymentAttemptUseCases(ctx["conn"]).retry(
            attempt_id,
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            idempotency_key=body.idempotency_key,
            request_id=ctx["request_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return _attempt_out(attempt)


# ── Payments ───────────────────────────────────────────────────────────────────

@billing_router.get("/payments", response_model=PaginatedPayments)
def list_payments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_org_billing_permission("payment.view")),
) -> PaginatedPayments:
    p, ps, offset = _page(page, page_size)
    items, total = PaymentUseCases(ctx["conn"]).list(
        organization_id=ctx["organization_id"], limit=ps, offset=offset,
    )
    return PaginatedPayments(
        items=[PaymentOut(**pay.__dict__) for pay in items],
        total=total, page=p, page_size=ps,
    )


@billing_router.get("/payments/{payment_id}", response_model=PaymentOut)
def get_payment(
    payment_id: int,
    ctx: dict = Depends(require_org_billing_permission("payment.view")),
) -> PaymentOut:
    try:
        pay = PaymentUseCases(ctx["conn"]).get(payment_id, organization_id=ctx["organization_id"])
    except BillingError as e:
        raise_billing_http(e)
    return PaymentOut(**pay.__dict__)


@billing_router.post("/payments/{payment_id}/settle", response_model=PaymentOut)
def settle_payment(
    payment_id: int,
    ctx: dict = Depends(require_org_billing_permission("payment.manage")),
) -> PaymentOut:
    try:
        pay = PaymentUseCases(ctx["conn"]).settle(
            payment_id,
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            request_id=ctx["request_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return PaymentOut(**pay.__dict__)


@billing_router.post("/payments/{payment_id}/reconcile", response_model=PaymentOut)
def reconcile_payment(
    payment_id: int,
    ctx: dict = Depends(require_org_billing_permission("payment.manage")),
) -> PaymentOut:
    try:
        pay = PaymentUseCases(ctx["conn"]).reconcile(
            payment_id,
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            request_id=ctx["request_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return PaymentOut(**pay.__dict__)


@billing_router.post("/payments/{payment_id}/allocate", response_model=PaymentAllocationOut)
def allocate_payment(
    payment_id: int,
    body: PaymentAllocateRequest,
    ctx: dict = Depends(require_org_billing_permission("payment.manage")),
) -> PaymentAllocationOut:
    try:
        alloc = PaymentUseCases(ctx["conn"]).allocate(
            payment_id,
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            invoice_id=body.invoice_id,
            amount=body.amount,
            request_id=ctx["request_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return PaymentAllocationOut(**alloc.__dict__)


@billing_router.post("/payments/{payment_id}/reverse", response_model=PaymentOut)
def reverse_payment(
    payment_id: int,
    body: PaymentReverseRequest,
    ctx: dict = Depends(require_org_billing_permission("payment.manage")),
) -> PaymentOut:
    try:
        pay = PaymentUseCases(ctx["conn"]).reverse(
            payment_id,
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            reason=body.reason,
            request_id=ctx["request_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return PaymentOut(**pay.__dict__)


# ── Manual Transfer ────────────────────────────────────────────────────────────

@billing_router.post("/manual-transfer", response_model=PaymentOut, status_code=201)
def create_manual_transfer(
    body: ManualTransferRequest,
    ctx: dict = Depends(require_org_billing_permission("payment.manage")),
) -> PaymentOut:
    try:
        pay = PaymentUseCases(ctx["conn"]).record_manual(
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            invoice_id=body.invoice_id,
            amount=body.amount,
            currency=body.currency,
            idempotency_key=body.idempotency_key,
            notes=body.notes,
            request_id=ctx["request_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return PaymentOut(**pay.__dict__)


# ── Refunds ────────────────────────────────────────────────────────────────────

@billing_router.get("/refunds", response_model=PaginatedRefunds)
def list_refunds(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_org_billing_permission("payment.view")),
) -> PaginatedRefunds:
    p, ps, offset = _page(page, page_size)
    items, total = RefundUseCases(ctx["conn"]).list(
        organization_id=ctx["organization_id"], limit=ps, offset=offset,
    )
    return PaginatedRefunds(
        items=[RefundOut(**r.__dict__) for r in items],
        total=total, page=p, page_size=ps,
    )


@billing_router.post("/refunds", response_model=RefundOut, status_code=201)
def create_refund(
    body: RefundCreateRequest,
    ctx: dict = Depends(require_org_billing_permission("refund.manage")),
) -> RefundOut:
    try:
        refund = RefundUseCases(ctx["conn"]).create(
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            payment_id=body.payment_id,
            amount=body.amount,
            reason=body.reason,
            request_id=ctx["request_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return RefundOut(**refund.__dict__)


# ── Credit Notes ───────────────────────────────────────────────────────────────

@billing_router.get("/credit-notes", response_model=PaginatedCreditNotes)
def list_credit_notes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_org_billing_permission("invoice.view")),
) -> PaginatedCreditNotes:
    p, ps, offset = _page(page, page_size)
    items, total = CreditNoteUseCases(ctx["conn"]).list(
        organization_id=ctx["organization_id"], limit=ps, offset=offset,
    )
    return PaginatedCreditNotes(
        items=[CreditNoteOut(**cn.__dict__) for cn in items],
        total=total, page=p, page_size=ps,
    )


@billing_router.post("/credit-notes", response_model=CreditNoteOut, status_code=201)
def create_credit_note(
    body: CreditNoteCreateRequest,
    ctx: dict = Depends(require_org_billing_permission("credit_note.manage")),
) -> CreditNoteOut:
    try:
        cn = CreditNoteUseCases(ctx["conn"]).create(
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            invoice_id=body.invoice_id,
            amount=body.amount,
            reason=body.reason,
            request_id=ctx["request_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return CreditNoteOut(**cn.__dict__)


@billing_router.post("/credit-notes/{cn_id}/apply", response_model=CreditNoteOut)
def apply_credit_note(
    cn_id: int,
    ctx: dict = Depends(require_org_billing_permission("credit_note.manage")),
) -> CreditNoteOut:
    try:
        cn = CreditNoteUseCases(ctx["conn"]).apply(
            cn_id,
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            request_id=ctx["request_id"],
        )
    except BillingError as e:
        raise_billing_http(e)
    return CreditNoteOut(**cn.__dict__)


# ── Ledger ─────────────────────────────────────────────────────────────────────

@billing_router.get("/ledger", response_model=PaginatedLedger)
def list_ledger(
    entry_type: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    ctx: dict = Depends(require_org_billing_permission("billing.view")),
) -> PaginatedLedger:
    p, ps, offset = _page(page, page_size, max_size=200)
    items, total = LedgerUseCases(ctx["conn"]).list(
        organization_id=ctx["organization_id"],
        entry_type=entry_type,
        limit=ps,
        offset=offset,
    )
    return PaginatedLedger(
        items=[LedgerEntryOut(**e.__dict__) for e in items],
        total=total, page=p, page_size=ps,
    )


# ── Provider Events ────────────────────────────────────────────────────────────

@billing_router.post("/provider-events", response_model=ProviderEventOut, status_code=201)
def receive_provider_event(
    body: ProviderEventRequest,
) -> ProviderEventOut:
    """Webhook receiver — idempotent by provider_event_id.

    Conceptual signature verification: when ``signature`` is provided, it is
    checked with HMAC-SHA256 against BILLING_WEBHOOK_SECRET (or a fixed academic
    secret for mock). Invalid signatures are rejected. No bearer auth.
    """
    import os

    from fastapi import HTTPException

    from app.core.database import using_write_conn
    from app.packages.billing.domain.providers import get_provider

    if body.signature is not None:
        secret = os.environ.get("BILLING_WEBHOOK_SECRET", "academic-dev-webhook-secret")
        provider = get_provider(body.provider_code)
        payload = (
            f"{body.provider_code}|{body.provider_event_id}|{body.event_type}|"
            f"{body.payload or ''}"
        ).encode("utf-8")
        if not provider.verify_webhook_signature(
            payload=payload,
            signature_header=body.signature,
            secret=secret,
        ):
            raise HTTPException(status_code=401, detail="Invalid provider webhook signature")

    with using_write_conn() as conn:
        event = ProviderEventUseCases(conn).process(
            provider_code=body.provider_code,
            provider_event_id=body.provider_event_id,
            event_type=body.event_type,
            payload=body.payload,
        )
    return ProviderEventOut(
        id=event.id, provider_code=event.provider_code,
        provider_event_id=event.provider_event_id,
        event_type=event.event_type, processed=event.processed,
        created_at=event.created_at,
    )
