"""Billing consolidated use cases — Spec 019.

Covers: BillingProfile, Invoice lifecycle, PaymentAttempt, Payment,
        PaymentAllocation, Refund, CreditNote, ProviderEvent, Ledger.

Subscription orchestration via billing.application.orchestration (no circular imports).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.billing.domain.entities import (
    BillingLedgerEntry,
    BillingProfile,
    CreditNote,
    Invoice,
    InvoiceItem,
    Payment,
    PaymentAllocation,
    PaymentAttempt,
    PaymentMethodReference,
    PaymentProviderEvent,
    Refund,
)
from app.packages.billing.domain.errors import (
    BillingProfileExistsError,
    ConflictError,
    CurrencyMismatchError,
    IdempotencyConflictError,
    InsufficientFundsError,
    InvalidTransitionError,
    InvoiceImmutableError,
    LedgerImmutableError,
    NotFoundError,
    ValidationError,
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    row = conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()
    return int(row[0])


def _now() -> datetime:
    return utc_now()


def _audit(
    conn: duckdb.DuckDBPyConnection,
    *,
    action: str,
    target_type: str,
    target_id: str,
    actor_user_id: int,
    organization_id: Optional[int] = None,
    previous_values: Optional[dict[str, Any]] = None,
    new_values: Optional[dict[str, Any]] = None,
    reason: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    try:
        from app.packages.organizations.infrastructure.repositories.audit_repository import (
            AuditRepository,
        )

        AuditRepository(conn).append(
            action=action,
            target_type=target_type,
            target_id=target_id,
            source="billing.use_case",
            result="success",
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            previous_values=previous_values,
            new_values=new_values,
            reason=reason,
            request_id=request_id,
        )
    except Exception:
        pass


# ── Column lists ───────────────────────────────────────────────────────────────

_PROFILE_COLS = (
    "id, organization_id, default_currency, legal_name, tax_id, "
    "billing_address, email, status, created_at, updated_at"
)

_INVOICE_COLS = (
    "id, organization_id, billing_profile_id, subscription_id, "
    "invoice_number, currency, status, subtotal, total, amount_paid, amount_due, "
    "period_start, period_end, due_date, issued_at, paid_at, voided_at, "
    "notes, created_at, updated_at"
)

_ITEM_COLS = (
    "id, invoice_id, description, quantity, unit_price, amount, "
    "period_start, period_end, created_at"
)

_METHOD_COLS = (
    "id, organization_id, provider_code, display_label, token_ref, "
    "method_type, is_default, status, created_at, updated_at"
)

_ATTEMPT_COLS = (
    "id, organization_id, invoice_id, payment_method_ref_id, provider_code, "
    "idempotency_key, amount, currency, status, provider_attempt_id, "
    "failure_reason, created_at, updated_at"
)

_PAYMENT_COLS = (
    "id, organization_id, payment_attempt_id, provider_code, amount, currency, "
    "status, provider_payment_id, settled_at, reconciled_at, created_at, updated_at"
)

_ALLOC_COLS = (
    "id, payment_id, invoice_id, organization_id, amount, created_at"
)

_REFUND_COLS = (
    "id, organization_id, payment_id, amount, currency, reason, "
    "status, processed_at, created_at, updated_at"
)

_CN_COLS = (
    "id, organization_id, invoice_id, credit_note_number, amount, currency, "
    "reason, status, issued_at, applied_at, created_at, updated_at"
)

_EVENT_COLS = (
    "id, provider_code, provider_event_id, event_type, payload, "
    "processed, processed_at, created_at"
)

_LEDGER_COLS = (
    "id, organization_id, entry_type, reference_type, reference_id, "
    "amount, currency, description, created_at"
)


# ── Mappers ────────────────────────────────────────────────────────────────────


def _map_profile(r: tuple) -> BillingProfile:
    return BillingProfile(
        id=int(r[0]), organization_id=int(r[1]), default_currency=str(r[2]),
        legal_name=r[3], tax_id=r[4], billing_address=r[5], email=r[6],
        status=str(r[7]), created_at=r[8], updated_at=r[9],
    )


def _map_invoice(r: tuple) -> Invoice:
    return Invoice(
        id=int(r[0]), organization_id=int(r[1]), billing_profile_id=int(r[2]),
        subscription_id=int(r[3]) if r[3] is not None else None,
        invoice_number=str(r[4]), currency=str(r[5]), status=str(r[6]),
        subtotal=Decimal(str(r[7])), total=Decimal(str(r[8])),
        amount_paid=Decimal(str(r[9])), amount_due=Decimal(str(r[10])),
        period_start=r[11], period_end=r[12], due_date=r[13],
        issued_at=r[14], paid_at=r[15], voided_at=r[16],
        notes=r[17], created_at=r[18], updated_at=r[19],
    )


def _map_item(r: tuple) -> InvoiceItem:
    return InvoiceItem(
        id=int(r[0]), invoice_id=int(r[1]), description=str(r[2]),
        quantity=Decimal(str(r[3])), unit_price=Decimal(str(r[4])),
        amount=Decimal(str(r[5])), period_start=r[6], period_end=r[7],
        created_at=r[8],
    )


def _map_method(r: tuple) -> PaymentMethodReference:
    return PaymentMethodReference(
        id=int(r[0]), organization_id=int(r[1]), provider_code=str(r[2]),
        display_label=str(r[3]), token_ref=str(r[4]), method_type=str(r[5]),
        is_default=bool(r[6]), status=str(r[7]), created_at=r[8], updated_at=r[9],
    )


def _map_attempt(r: tuple) -> PaymentAttempt:
    return PaymentAttempt(
        id=int(r[0]), organization_id=int(r[1]), invoice_id=int(r[2]),
        payment_method_ref_id=int(r[3]) if r[3] is not None else None,
        provider_code=str(r[4]), idempotency_key=str(r[5]),
        amount=Decimal(str(r[6])), currency=str(r[7]), status=str(r[8]),
        provider_attempt_id=r[9], failure_reason=r[10],
        created_at=r[11], updated_at=r[12],
    )


def _map_payment(r: tuple) -> Payment:
    return Payment(
        id=int(r[0]), organization_id=int(r[1]), payment_attempt_id=int(r[2]),
        provider_code=str(r[3]), amount=Decimal(str(r[4])), currency=str(r[5]),
        status=str(r[6]), provider_payment_id=r[7],
        settled_at=r[8], reconciled_at=r[9], created_at=r[10], updated_at=r[11],
    )


def _map_alloc(r: tuple) -> PaymentAllocation:
    return PaymentAllocation(
        id=int(r[0]), payment_id=int(r[1]), invoice_id=int(r[2]),
        organization_id=int(r[3]), amount=Decimal(str(r[4])), created_at=r[5],
    )


def _map_refund(r: tuple) -> Refund:
    return Refund(
        id=int(r[0]), organization_id=int(r[1]), payment_id=int(r[2]),
        amount=Decimal(str(r[3])), currency=str(r[4]), reason=r[5],
        status=str(r[6]), processed_at=r[7], created_at=r[8], updated_at=r[9],
    )


def _map_cn(r: tuple) -> CreditNote:
    return CreditNote(
        id=int(r[0]), organization_id=int(r[1]), invoice_id=int(r[2]),
        credit_note_number=str(r[3]), amount=Decimal(str(r[4])),
        currency=str(r[5]), reason=r[6], status=str(r[7]),
        issued_at=r[8], applied_at=r[9], created_at=r[10], updated_at=r[11],
    )


def _map_event(r: tuple) -> PaymentProviderEvent:
    return PaymentProviderEvent(
        id=int(r[0]), provider_code=str(r[1]), provider_event_id=str(r[2]),
        event_type=str(r[3]), payload=r[4], processed=bool(r[5]),
        processed_at=r[6], created_at=r[7],
    )


def _map_ledger(r: tuple) -> BillingLedgerEntry:
    return BillingLedgerEntry(
        id=int(r[0]), organization_id=int(r[1]), entry_type=str(r[2]),
        reference_type=str(r[3]), reference_id=int(r[4]),
        amount=Decimal(str(r[5])), currency=str(r[6]),
        description=r[7], created_at=r[8],
    )


# ── Ledger helper ──────────────────────────────────────────────────────────────


def _append_ledger(
    conn: duckdb.DuckDBPyConnection,
    *,
    organization_id: int,
    entry_type: str,
    reference_type: str,
    reference_id: int,
    amount: Decimal,
    currency: str,
    description: Optional[str] = None,
) -> BillingLedgerEntry:
    now = _now()
    lid = _next_id(conn, "app_billing_ledger_entry")
    conn.execute(
        f"INSERT INTO app_billing_ledger_entry ({_LEDGER_COLS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [lid, organization_id, entry_type, reference_type, reference_id,
         str(amount), currency, description, now],
    )
    row = conn.execute(
        f"SELECT {_LEDGER_COLS} FROM app_billing_ledger_entry WHERE id = ?", [lid]
    ).fetchone()
    return _map_ledger(row)


# ── Invoice number generator ───────────────────────────────────────────────────


def _generate_invoice_number(conn: duckdb.DuckDBPyConnection) -> str:
    count = int(
        conn.execute("SELECT COUNT(*) FROM app_invoice").fetchone()[0]
    )
    return f"INV-{count + 1:06d}"


def _generate_cn_number(conn: duckdb.DuckDBPyConnection) -> str:
    count = int(
        conn.execute("SELECT COUNT(*) FROM app_credit_note").fetchone()[0]
    )
    return f"CN-{count + 1:06d}"


# ── BillingProfile Use Cases ───────────────────────────────────────────────────


class BillingProfileUseCases:
    """CreateBillingProfile, UpdateBillingProfile, GetBillingProfile."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        organization_id: int,
        default_currency: str,
        legal_name: Optional[str] = None,
        tax_id: Optional[str] = None,
        billing_address: Optional[str] = None,
        email: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> BillingProfile:
        if not default_currency or len(default_currency.strip()) != 3:
            raise ValidationError("default_currency must be a 3-char ISO code")

        existing = self._conn.execute(
            "SELECT 1 FROM app_billing_profile WHERE organization_id = ?",
            [organization_id],
        ).fetchone()
        if existing:
            raise BillingProfileExistsError(
                f"Billing profile already exists for organization {organization_id}"
            )

        now = _now()
        pid = _next_id(self._conn, "app_billing_profile")
        self._conn.execute(
            f"INSERT INTO app_billing_profile ({_PROFILE_COLS}) VALUES (?,?,?,?,?,?,?,'active',?,?)",
            [pid, organization_id, default_currency.strip().upper(),
             legal_name, tax_id, billing_address, email, now, now],
        )
        profile = self._get_or_raise_by_org(organization_id)
        _audit(
            self._conn, action="billing_profile.created",
            target_type="billing_profile", target_id=str(pid),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"default_currency": default_currency},
            request_id=request_id,
        )
        return profile

    def update(
        self,
        organization_id: int,
        *,
        actor_user_id: int,
        legal_name: Optional[str] = None,
        tax_id: Optional[str] = None,
        billing_address: Optional[str] = None,
        email: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> BillingProfile:
        profile = self._get_or_raise_by_org(organization_id)
        now = _now()
        self._conn.execute(
            """
            UPDATE app_billing_profile SET
                legal_name = COALESCE(?, legal_name),
                tax_id = COALESCE(?, tax_id),
                billing_address = COALESCE(?, billing_address),
                email = COALESCE(?, email),
                updated_at = ?
            WHERE organization_id = ?
            """,
            [legal_name, tax_id, billing_address, email, now, organization_id],
        )
        return self._get_or_raise_by_org(organization_id)

    def get_by_org(self, organization_id: int) -> BillingProfile:
        return self._get_or_raise_by_org(organization_id)

    def _get_or_raise_by_org(self, organization_id: int) -> BillingProfile:
        row = self._conn.execute(
            f"SELECT {_PROFILE_COLS} FROM app_billing_profile WHERE organization_id = ?",
            [organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"billing_profile for organization {organization_id}")
        return _map_profile(row)


# ── Invoice Use Cases ──────────────────────────────────────────────────────────


class InvoiceUseCases:
    """CreateInvoice (draft), AddInvoiceItem, IssueInvoice, VoidInvoice, MarkInvoicePastDue."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        organization_id: int,
        billing_profile_id: int,
        subscription_id: Optional[int] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        due_date: Optional[date] = None,
        notes: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Invoice:
        profile_row = self._conn.execute(
            "SELECT default_currency, status FROM app_billing_profile WHERE id = ? AND organization_id = ?",
            [billing_profile_id, organization_id],
        ).fetchone()
        if not profile_row:
            raise NotFoundError(f"billing_profile id={billing_profile_id}")
        if str(profile_row[1]) == "suspended":
            raise InvalidTransitionError("Billing profile is suspended")

        currency = str(profile_row[0])
        now = _now()
        inv_num = _generate_invoice_number(self._conn)
        iid = _next_id(self._conn, "app_invoice")
        self._conn.execute(
            f"""
            INSERT INTO app_invoice ({_INVOICE_COLS})
            VALUES (?,?,?,?,?,?,'draft',0,0,0,0,?,?,?,NULL,NULL,NULL,?,?,?)
            """,
            [iid, organization_id, billing_profile_id, subscription_id,
             inv_num, currency, period_start, period_end, due_date, notes, now, now],
        )
        inv = self._get_or_raise(iid)
        _audit(
            self._conn, action="invoice.created",
            target_type="invoice", target_id=str(iid),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"invoice_number": inv_num, "currency": currency},
            request_id=request_id,
        )
        return inv

    def add_item(
        self,
        invoice_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        description: str,
        quantity: Decimal,
        unit_price: Decimal,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
    ) -> InvoiceItem:
        inv = self._get_or_raise_for_org(invoice_id, organization_id)
        if inv.status != "draft":
            raise InvoiceImmutableError(
                f"Cannot add items to invoice in status={inv.status}"
            )
        if not description or not description.strip():
            raise ValidationError("description is required")
        if quantity <= 0:
            raise ValidationError("quantity must be > 0")
        if unit_price < 0:
            raise ValidationError("unit_price must be >= 0")

        amount = quantity * unit_price
        now = _now()
        item_id = _next_id(self._conn, "app_invoice_item")
        self._conn.execute(
            f"INSERT INTO app_invoice_item ({_ITEM_COLS}) VALUES (?,?,?,?,?,?,?,?,?)",
            [item_id, invoice_id, description.strip(), str(quantity),
             str(unit_price), str(amount), period_start, period_end, now],
        )
        self._recalculate_totals(invoice_id)
        row = self._conn.execute(
            f"SELECT {_ITEM_COLS} FROM app_invoice_item WHERE id = ?", [item_id]
        ).fetchone()
        return _map_item(row)

    def issue(
        self,
        invoice_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        request_id: Optional[str] = None,
    ) -> Invoice:
        inv = self._get_or_raise_for_org(invoice_id, organization_id)
        if inv.status != "draft":
            raise InvalidTransitionError(
                f"Invoice must be draft to issue (status={inv.status})"
            )
        items = self._conn.execute(
            "SELECT COUNT(*) FROM app_invoice_item WHERE invoice_id = ?", [invoice_id]
        ).fetchone()[0]
        if int(items) == 0:
            raise ValidationError("Cannot issue invoice with no items")

        now = _now()
        self._conn.execute(
            "UPDATE app_invoice SET status='issued', issued_at=?, updated_at=? WHERE id=?",
            [now, now, invoice_id],
        )
        inv = self._get_or_raise(invoice_id)
        _append_ledger(
            self._conn,
            organization_id=organization_id,
            entry_type="invoice_issued",
            reference_type="invoice",
            reference_id=invoice_id,
            amount=inv.total,
            currency=inv.currency,
            description=f"Invoice {inv.invoice_number} issued",
        )
        _audit(
            self._conn, action="invoice.issued",
            target_type="invoice", target_id=str(invoice_id),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"status": "issued", "total": str(inv.total)},
            request_id=request_id,
        )
        return inv

    def void(
        self,
        invoice_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Invoice:
        inv = self._get_or_raise_for_org(invoice_id, organization_id)
        if inv.status not in ("draft", "issued", "past_due"):
            raise InvalidTransitionError(
                f"Cannot void invoice in status={inv.status}"
            )
        now = _now()
        self._conn.execute(
            "UPDATE app_invoice SET status='void', voided_at=?, updated_at=? WHERE id=?",
            [now, now, invoice_id],
        )
        _audit(
            self._conn, action="invoice.voided",
            target_type="invoice", target_id=str(invoice_id),
            actor_user_id=actor_user_id, organization_id=organization_id,
            previous_values={"status": inv.status},
            new_values={"status": "void"},
            reason=reason,
            request_id=request_id,
        )
        return self._get_or_raise(invoice_id)

    def mark_past_due(
        self,
        invoice_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        request_id: Optional[str] = None,
    ) -> Invoice:
        inv = self._get_or_raise_for_org(invoice_id, organization_id)
        if inv.status not in ("issued", "partially_paid"):
            raise InvalidTransitionError(
                f"Cannot mark invoice past_due from status={inv.status}"
            )
        now = _now()
        self._conn.execute(
            "UPDATE app_invoice SET status='past_due', updated_at=? WHERE id=?",
            [now, invoice_id],
        )
        updated = self._get_or_raise(invoice_id)
        if updated.subscription_id:
            from app.packages.billing.application.orchestration import (
                notify_subscription_past_due,
            )
            notify_subscription_past_due(
                self._conn,
                subscription_id=updated.subscription_id,
                actor_user_id=actor_user_id,
                request_id=request_id,
            )
        _audit(
            self._conn, action="invoice.past_due",
            target_type="invoice", target_id=str(invoice_id),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"status": "past_due"},
            request_id=request_id,
        )
        return updated

    def get(self, invoice_id: int, *, organization_id: int) -> Invoice:
        return self._get_or_raise_for_org(invoice_id, organization_id)

    def list(
        self,
        *,
        organization_id: int,
        status: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[Invoice], int]:
        conditions = ["organization_id = ?"]
        params: list[Any] = [organization_id]
        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        where = " AND ".join(conditions)
        total = int(
            self._conn.execute(
                f"SELECT COUNT(*) FROM app_invoice WHERE {where}", params
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_INVOICE_COLS} FROM app_invoice WHERE {where} "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [_map_invoice(r) for r in rows], total

    def list_items(self, invoice_id: int) -> list[InvoiceItem]:
        rows = self._conn.execute(
            f"SELECT {_ITEM_COLS} FROM app_invoice_item WHERE invoice_id = ? ORDER BY id ASC",
            [invoice_id],
        ).fetchall()
        return [_map_item(r) for r in rows]

    def _recalculate_totals(self, invoice_id: int) -> None:
        row = self._conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM app_invoice_item WHERE invoice_id = ?",
            [invoice_id],
        ).fetchone()
        total = Decimal(str(row[0]))
        now = _now()
        self._conn.execute(
            "SELECT amount_paid FROM app_invoice WHERE id = ?", [invoice_id]
        )
        paid_row = self._conn.execute(
            "SELECT amount_paid FROM app_invoice WHERE id = ?", [invoice_id]
        ).fetchone()
        amount_paid = Decimal(str(paid_row[0])) if paid_row else Decimal("0")
        amount_due = max(total - amount_paid, Decimal("0"))
        self._conn.execute(
            "UPDATE app_invoice SET subtotal=?, total=?, amount_due=?, updated_at=? WHERE id=?",
            [str(total), str(total), str(amount_due), now, invoice_id],
        )

    def _get_or_raise(self, invoice_id: int) -> Invoice:
        row = self._conn.execute(
            f"SELECT {_INVOICE_COLS} FROM app_invoice WHERE id = ?", [invoice_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"invoice id={invoice_id}")
        return _map_invoice(row)

    def _get_or_raise_for_org(self, invoice_id: int, organization_id: int) -> Invoice:
        row = self._conn.execute(
            f"SELECT {_INVOICE_COLS} FROM app_invoice WHERE id = ? AND organization_id = ?",
            [invoice_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"invoice id={invoice_id}")
        return _map_invoice(row)


# ── PaymentMethodReference Use Cases ───────────────────────────────────────────


class PaymentMethodUseCases:
    """CreatePaymentMethodReference (no PAN/CVV), ListMethods, RemoveMethod."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        organization_id: int,
        provider_code: str,
        display_label: str,
        token_ref: str,
        method_type: str,
        is_default: bool = False,
        request_id: Optional[str] = None,
    ) -> PaymentMethodReference:
        if not token_ref or not token_ref.strip():
            raise ValidationError("token_ref is required")
        if method_type not in ("card", "bank_transfer", "mock"):
            raise ValidationError("method_type must be card, bank_transfer, or mock")

        now = _now()
        mid = _next_id(self._conn, "app_payment_method_reference")
        self._conn.execute(
            f"INSERT INTO app_payment_method_reference ({_METHOD_COLS}) VALUES (?,?,?,?,?,?,?,'active',?,?)",
            [mid, organization_id, provider_code, display_label,
             token_ref.strip(), method_type, is_default, now, now],
        )
        row = self._conn.execute(
            f"SELECT {_METHOD_COLS} FROM app_payment_method_reference WHERE id = ?", [mid]
        ).fetchone()
        return _map_method(row)

    def list(self, organization_id: int) -> list[PaymentMethodReference]:
        rows = self._conn.execute(
            f"SELECT {_METHOD_COLS} FROM app_payment_method_reference "
            "WHERE organization_id = ? AND status = 'active' ORDER BY is_default DESC, id ASC",
            [organization_id],
        ).fetchall()
        return [_map_method(r) for r in rows]

    def remove(self, method_id: int, *, organization_id: int, actor_user_id: int) -> None:
        row = self._conn.execute(
            "SELECT id FROM app_payment_method_reference WHERE id = ? AND organization_id = ?",
            [method_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"payment_method_reference id={method_id}")
        now = _now()
        self._conn.execute(
            "UPDATE app_payment_method_reference SET status='removed', updated_at=? WHERE id=?",
            [now, method_id],
        )


# ── PaymentAttempt Use Cases ───────────────────────────────────────────────────


class PaymentAttemptUseCases:
    """CreatePaymentAttempt (idempotent), ConfirmMockPayment, CancelAttempt, RetryPayment."""

    MOCK_PROVIDER = "academic_mock"
    MANUAL_PROVIDER = "manual_transfer"

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        organization_id: int,
        invoice_id: int,
        provider_code: str,
        idempotency_key: str,
        amount: Decimal,
        currency: str,
        payment_method_ref_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> PaymentAttempt:
        existing = self._conn.execute(
            f"SELECT {_ATTEMPT_COLS} FROM app_payment_attempt WHERE idempotency_key = ?",
            [idempotency_key],
        ).fetchone()
        if existing:
            return _map_attempt(existing)

        inv_row = self._conn.execute(
            "SELECT id, status, currency, organization_id FROM app_invoice WHERE id = ? AND organization_id = ?",
            [invoice_id, organization_id],
        ).fetchone()
        if not inv_row:
            raise NotFoundError(f"invoice id={invoice_id}")
        if str(inv_row[1]) in ("void", "paid", "credited"):
            raise InvalidTransitionError(
                f"Cannot create attempt for invoice in status={inv_row[1]}"
            )
        if str(inv_row[2]) != currency.strip().upper():
            raise CurrencyMismatchError(
                f"Invoice currency {inv_row[2]} != attempt currency {currency}"
            )
        if amount <= 0:
            raise ValidationError("amount must be > 0")

        now = _now()
        aid = _next_id(self._conn, "app_payment_attempt")
        self._conn.execute(
            f"""
            INSERT INTO app_payment_attempt ({_ATTEMPT_COLS})
            VALUES (?,?,?,?,?,?,?,?,'created',NULL,NULL,?,?)
            """,
            [aid, organization_id, invoice_id, payment_method_ref_id,
             provider_code, idempotency_key, str(amount), currency.strip().upper(),
             now, now],
        )
        attempt = self._get_or_raise(aid)
        _audit(
            self._conn, action="payment_attempt.created",
            target_type="payment_attempt", target_id=str(aid),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"provider_code": provider_code, "amount": str(amount)},
            request_id=request_id,
        )
        return attempt

    def confirm_mock(
        self,
        attempt_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        request_id: Optional[str] = None,
    ) -> PaymentAttempt:
        """Confirm an academic_mock payment attempt → creates Payment record."""
        attempt = self._get_or_raise_for_org(attempt_id, organization_id)
        if attempt.provider_code != self.MOCK_PROVIDER:
            raise ValidationError("confirm_mock only valid for academic_mock provider")
        if attempt.status not in ("created", "processing"):
            raise InvalidTransitionError(
                f"Cannot confirm attempt in status={attempt.status}"
            )

        now = _now()
        provider_attempt_id = f"mock_{uuid.uuid4().hex[:12]}"
        self._conn.execute(
            """
            UPDATE app_payment_attempt SET
                status='succeeded', provider_attempt_id=?, updated_at=?
            WHERE id=?
            """,
            [provider_attempt_id, now, attempt_id],
        )
        updated_attempt = self._get_or_raise(attempt_id)

        # Create payment record
        pay_id = _next_id(self._conn, "app_payment")
        self._conn.execute(
            f"""
            INSERT INTO app_payment ({_PAYMENT_COLS})
            VALUES (?,?,?,?[MOCK],?,?,'recorded',?,NULL,NULL,?,?)
            """.replace("?[MOCK]", "?"),
            [pay_id, organization_id, attempt_id, self.MOCK_PROVIDER,
             str(attempt.amount), attempt.currency, provider_attempt_id, now, now],
        )
        _append_ledger(
            self._conn,
            organization_id=organization_id,
            entry_type="payment_received",
            reference_type="payment",
            reference_id=pay_id,
            amount=attempt.amount,
            currency=attempt.currency,
            description=f"[MOCK] Payment {provider_attempt_id}",
        )
        _audit(
            self._conn, action="payment_attempt.confirmed_mock",
            target_type="payment_attempt", target_id=str(attempt_id),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"status": "succeeded", "payment_id": pay_id},
            request_id=request_id,
        )
        return updated_attempt

    def cancel(
        self,
        attempt_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
    ) -> PaymentAttempt:
        attempt = self._get_or_raise_for_org(attempt_id, organization_id)
        if attempt.status not in ("created",):
            raise InvalidTransitionError(
                f"Cannot cancel attempt in status={attempt.status}"
            )
        now = _now()
        self._conn.execute(
            "UPDATE app_payment_attempt SET status='canceled', updated_at=? WHERE id=?",
            [now, attempt_id],
        )
        return self._get_or_raise(attempt_id)

    def retry(
        self,
        attempt_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        idempotency_key: str,
        request_id: Optional[str] = None,
    ) -> PaymentAttempt:
        """RetryPayment — new attempt from a failed one (same invoice/amount/currency)."""
        failed = self._get_or_raise_for_org(attempt_id, organization_id)
        if failed.status != "failed":
            raise InvalidTransitionError(
                f"RetryPayment only allowed from failed attempts (got status={failed.status})"
            )
        return self.create(
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            invoice_id=failed.invoice_id,
            provider_code=failed.provider_code,
            idempotency_key=idempotency_key,
            amount=failed.amount,
            currency=failed.currency,
            payment_method_ref_id=failed.payment_method_ref_id,
            request_id=request_id,
        )

    def list(
        self,
        *,
        organization_id: int,
        invoice_id: Optional[int] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[PaymentAttempt], int]:
        conditions = ["organization_id = ?"]
        params: list[Any] = [organization_id]
        if invoice_id is not None:
            conditions.append("invoice_id = ?")
            params.append(invoice_id)
        where = " AND ".join(conditions)
        total = int(
            self._conn.execute(
                f"SELECT COUNT(*) FROM app_payment_attempt WHERE {where}", params
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_ATTEMPT_COLS} FROM app_payment_attempt WHERE {where} "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [_map_attempt(r) for r in rows], total

    def get(self, attempt_id: int, *, organization_id: int) -> PaymentAttempt:
        return self._get_or_raise_for_org(attempt_id, organization_id)

    def _get_or_raise(self, attempt_id: int) -> PaymentAttempt:
        row = self._conn.execute(
            f"SELECT {_ATTEMPT_COLS} FROM app_payment_attempt WHERE id = ?", [attempt_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"payment_attempt id={attempt_id}")
        return _map_attempt(row)

    def _get_or_raise_for_org(self, attempt_id: int, organization_id: int) -> PaymentAttempt:
        row = self._conn.execute(
            f"SELECT {_ATTEMPT_COLS} FROM app_payment_attempt WHERE id = ? AND organization_id = ?",
            [attempt_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"payment_attempt id={attempt_id}")
        return _map_attempt(row)


# ── Payment Use Cases ──────────────────────────────────────────────────────────


class PaymentUseCases:
    """RecordManualPayment, AllocatePayment, ReconcilePayment, ReversePayment."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def record_manual(
        self,
        *,
        actor_user_id: int,
        organization_id: int,
        invoice_id: int,
        amount: Decimal,
        currency: str,
        idempotency_key: Optional[str] = None,
        notes: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Payment:
        if idempotency_key:
            existing_attempt = self._conn.execute(
                f"SELECT {_ATTEMPT_COLS} FROM app_payment_attempt WHERE idempotency_key = ?",
                [idempotency_key],
            ).fetchone()
            if existing_attempt:
                attempt = _map_attempt(existing_attempt)
                pay_row = self._conn.execute(
                    f"SELECT {_PAYMENT_COLS} FROM app_payment WHERE payment_attempt_id = ?",
                    [attempt.id],
                ).fetchone()
                if pay_row:
                    return _map_payment(pay_row)

        inv_row = self._conn.execute(
            "SELECT id, status, currency FROM app_invoice WHERE id = ? AND organization_id = ?",
            [invoice_id, organization_id],
        ).fetchone()
        if not inv_row:
            raise NotFoundError(f"invoice id={invoice_id}")
        if str(inv_row[1]) in ("void", "paid", "credited"):
            raise InvalidTransitionError(f"Cannot pay invoice in status={inv_row[1]}")
        if str(inv_row[2]) != currency.strip().upper():
            raise CurrencyMismatchError(f"Invoice currency {inv_row[2]} != payment currency {currency}")
        if amount <= 0:
            raise ValidationError("amount must be > 0")

        ik = idempotency_key or f"manual_{uuid.uuid4().hex}"
        now = _now()

        attempt_id = _next_id(self._conn, "app_payment_attempt")
        self._conn.execute(
            f"""
            INSERT INTO app_payment_attempt ({_ATTEMPT_COLS})
            VALUES (?,?,?,NULL,'manual_transfer',?,?,?,'succeeded',NULL,NULL,?,?)
            """,
            [attempt_id, organization_id, invoice_id, ik, str(amount),
             currency.strip().upper(), now, now],
        )
        pay_id = _next_id(self._conn, "app_payment")
        self._conn.execute(
            f"""
            INSERT INTO app_payment ({_PAYMENT_COLS})
            VALUES (?,?,?,'manual_transfer',?,?,'recorded',NULL,NULL,NULL,?,?)
            """,
            [pay_id, organization_id, attempt_id, str(amount),
             currency.strip().upper(), now, now],
        )
        _append_ledger(
            self._conn,
            organization_id=organization_id,
            entry_type="payment_received",
            reference_type="payment",
            reference_id=pay_id,
            amount=amount,
            currency=currency.strip().upper(),
            description=notes or "Manual bank transfer",
        )
        payment = self._get_or_raise(pay_id)
        self._allocate_to_invoice(
            payment, invoice_id=invoice_id,
            amount=amount, organization_id=organization_id,
            actor_user_id=actor_user_id, request_id=request_id,
        )
        _audit(
            self._conn, action="payment.recorded_manual",
            target_type="payment", target_id=str(pay_id),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"amount": str(amount), "invoice_id": invoice_id},
            request_id=request_id,
        )
        return self._get_or_raise(pay_id)

    def allocate(
        self,
        payment_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        invoice_id: int,
        amount: Decimal,
        request_id: Optional[str] = None,
    ) -> PaymentAllocation:
        payment = self._get_or_raise_for_org(payment_id, organization_id)
        if payment.status == "reversed":
            raise InvalidTransitionError("Cannot allocate reversed payment")

        alloc = self._allocate_to_invoice(
            payment, invoice_id=invoice_id,
            amount=amount, organization_id=organization_id,
            actor_user_id=actor_user_id, request_id=request_id,
        )
        return alloc

    def settle(
        self,
        payment_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        request_id: Optional[str] = None,
    ) -> Payment:
        payment = self._get_or_raise_for_org(payment_id, organization_id)
        if payment.status != "recorded":
            raise InvalidTransitionError(
                f"Cannot settle payment in status={payment.status}"
            )
        now = _now()
        self._conn.execute(
            "UPDATE app_payment SET status='settled', settled_at=?, updated_at=? WHERE id=?",
            [now, now, payment_id],
        )
        _audit(
            self._conn, action="payment.settled",
            target_type="payment", target_id=str(payment_id),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"status": "settled"},
            request_id=request_id,
        )
        return self._get_or_raise(payment_id)

    def reconcile(
        self,
        payment_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        request_id: Optional[str] = None,
    ) -> Payment:
        payment = self._get_or_raise_for_org(payment_id, organization_id)
        if payment.status not in ("settled", "recorded"):
            raise InvalidTransitionError(
                f"Cannot reconcile payment in status={payment.status}"
            )
        now = _now()
        self._conn.execute(
            "UPDATE app_payment SET status='reconciled', reconciled_at=?, updated_at=? WHERE id=?",
            [now, now, payment_id],
        )
        # Check if linked invoice is now paid → recover subscription
        alloc_rows = self._conn.execute(
            "SELECT invoice_id FROM app_payment_allocation WHERE payment_id = ?",
            [payment_id],
        ).fetchall()
        for alloc_row in alloc_rows:
            inv_id = int(alloc_row[0])
            inv_row = self._conn.execute(
                "SELECT status, subscription_id FROM app_invoice WHERE id = ?", [inv_id]
            ).fetchone()
            if inv_row and str(inv_row[0]) == "paid" and inv_row[1] is not None:
                from app.packages.billing.application.orchestration import (
                    notify_subscription_recovered,
                )
                notify_subscription_recovered(
                    self._conn,
                    subscription_id=int(inv_row[1]),
                    actor_user_id=actor_user_id,
                    request_id=request_id,
                )
        _audit(
            self._conn, action="payment.reconciled",
            target_type="payment", target_id=str(payment_id),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"status": "reconciled"},
            request_id=request_id,
        )
        return self._get_or_raise(payment_id)

    def reverse(
        self,
        payment_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Payment:
        payment = self._get_or_raise_for_org(payment_id, organization_id)
        if payment.status not in ("recorded", "settled"):
            raise InvalidTransitionError(
                f"Cannot reverse payment in status={payment.status}"
            )
        now = _now()
        self._conn.execute(
            "UPDATE app_payment SET status='reversed', updated_at=? WHERE id=?",
            [now, payment_id],
        )
        _append_ledger(
            self._conn,
            organization_id=organization_id,
            entry_type="adjustment",
            reference_type="payment",
            reference_id=payment_id,
            amount=-payment.amount,
            currency=payment.currency,
            description=f"Reversal: {reason or 'no reason'}",
        )
        _audit(
            self._conn, action="payment.reversed",
            target_type="payment", target_id=str(payment_id),
            actor_user_id=actor_user_id, organization_id=organization_id,
            reason=reason,
            request_id=request_id,
        )
        return self._get_or_raise(payment_id)

    def list(
        self,
        *,
        organization_id: int,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[Payment], int]:
        total = int(
            self._conn.execute(
                "SELECT COUNT(*) FROM app_payment WHERE organization_id = ?", [organization_id]
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_PAYMENT_COLS} FROM app_payment WHERE organization_id = ? "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            [organization_id, limit, offset],
        ).fetchall()
        return [_map_payment(r) for r in rows], total

    def get(self, payment_id: int, *, organization_id: int) -> Payment:
        return self._get_or_raise_for_org(payment_id, organization_id)

    def _allocate_to_invoice(
        self,
        payment: Payment,
        *,
        invoice_id: int,
        amount: Decimal,
        organization_id: int,
        actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> PaymentAllocation:
        inv = self._conn.execute(
            "SELECT id, total, amount_paid, status, currency, subscription_id FROM app_invoice WHERE id = ? AND organization_id = ?",
            [invoice_id, organization_id],
        ).fetchone()
        if not inv:
            raise NotFoundError(f"invoice id={invoice_id}")
        if str(inv[3]) in ("void", "credited"):
            raise InvalidTransitionError(f"Cannot allocate to invoice in status={inv[3]}")

        inv_total = Decimal(str(inv[1]))
        inv_paid = Decimal(str(inv[2]))
        new_paid = inv_paid + amount
        new_due = max(inv_total - new_paid, Decimal("0"))

        if new_paid > inv_total + Decimal("0.0001"):
            raise InsufficientFundsError(
                f"Allocation {amount} would overpay invoice (total={inv_total}, already_paid={inv_paid})"
            )

        now = _now()
        alloc_id = _next_id(self._conn, "app_payment_allocation")
        self._conn.execute(
            f"INSERT INTO app_payment_allocation ({_ALLOC_COLS}) VALUES (?,?,?,?,?,?)",
            [alloc_id, payment.id, invoice_id, organization_id, str(amount), now],
        )

        if new_paid >= inv_total - Decimal("0.0001"):
            new_status = "paid"
        elif new_paid > Decimal("0"):
            new_status = "partially_paid"
        else:
            new_status = str(inv[3])

        self._conn.execute(
            "UPDATE app_invoice SET amount_paid=?, amount_due=?, status=?, updated_at=? WHERE id=?",
            [str(new_paid), str(new_due), new_status, now, invoice_id],
        )

        if new_status == "paid" and inv[5] is not None:
            from app.packages.billing.application.orchestration import (
                notify_subscription_recovered,
            )
            notify_subscription_recovered(
                self._conn,
                subscription_id=int(inv[5]),
                actor_user_id=actor_user_id,
                request_id=request_id,
            )

        row = self._conn.execute(
            f"SELECT {_ALLOC_COLS} FROM app_payment_allocation WHERE id = ?", [alloc_id]
        ).fetchone()
        return _map_alloc(row)

    def _get_or_raise(self, payment_id: int) -> Payment:
        row = self._conn.execute(
            f"SELECT {_PAYMENT_COLS} FROM app_payment WHERE id = ?", [payment_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"payment id={payment_id}")
        return _map_payment(row)

    def _get_or_raise_for_org(self, payment_id: int, organization_id: int) -> Payment:
        row = self._conn.execute(
            f"SELECT {_PAYMENT_COLS} FROM app_payment WHERE id = ? AND organization_id = ?",
            [payment_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"payment id={payment_id}")
        return _map_payment(row)


# ── Refund Use Cases ───────────────────────────────────────────────────────────


class RefundUseCases:
    """RefundPayment."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        organization_id: int,
        payment_id: int,
        amount: Decimal,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Refund:
        payment = self._conn.execute(
            f"SELECT {_PAYMENT_COLS} FROM app_payment WHERE id = ? AND organization_id = ?",
            [payment_id, organization_id],
        ).fetchone()
        if not payment:
            raise NotFoundError(f"payment id={payment_id}")
        payment = _map_payment(payment)
        if payment.status in ("reversed",):
            raise InvalidTransitionError("Cannot refund a reversed payment")
        if amount <= 0:
            raise ValidationError("amount must be > 0")
        if amount > payment.amount:
            raise InsufficientFundsError(
                f"Refund amount {amount} exceeds payment amount {payment.amount}"
            )

        now = _now()
        rid = _next_id(self._conn, "app_refund")
        self._conn.execute(
            f"INSERT INTO app_refund ({_REFUND_COLS}) VALUES (?,?,?,?,?,?,'pending',NULL,?,?)",
            [rid, organization_id, payment_id, str(amount), payment.currency, reason, now, now],
        )
        self._conn.execute(
            "UPDATE app_refund SET status='processed', processed_at=?, updated_at=? WHERE id=?",
            [now, now, rid],
        )
        new_pay_status = "refunded" if amount >= payment.amount else "partially_refunded"
        self._conn.execute(
            "UPDATE app_payment SET status=?, updated_at=? WHERE id=?",
            [new_pay_status, now, payment_id],
        )
        _append_ledger(
            self._conn,
            organization_id=organization_id,
            entry_type="refund_issued",
            reference_type="refund",
            reference_id=rid,
            amount=-amount,
            currency=payment.currency,
            description=reason or "Refund",
        )
        _audit(
            self._conn, action="refund.processed",
            target_type="refund", target_id=str(rid),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"amount": str(amount), "payment_id": payment_id},
            reason=reason,
            request_id=request_id,
        )
        row = self._conn.execute(
            f"SELECT {_REFUND_COLS} FROM app_refund WHERE id = ?", [rid]
        ).fetchone()
        return _map_refund(row)

    def list(
        self,
        *,
        organization_id: int,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[Refund], int]:
        total = int(
            self._conn.execute(
                "SELECT COUNT(*) FROM app_refund WHERE organization_id = ?", [organization_id]
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_REFUND_COLS} FROM app_refund WHERE organization_id = ? "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            [organization_id, limit, offset],
        ).fetchall()
        return [_map_refund(r) for r in rows], total


# ── CreditNote Use Cases ───────────────────────────────────────────────────────


class CreditNoteUseCases:
    """CreateCreditNote, ApplyCreditNote."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        organization_id: int,
        invoice_id: int,
        amount: Decimal,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> CreditNote:
        inv = self._conn.execute(
            "SELECT total, currency, status FROM app_invoice WHERE id = ? AND organization_id = ?",
            [invoice_id, organization_id],
        ).fetchone()
        if not inv:
            raise NotFoundError(f"invoice id={invoice_id}")
        if str(inv[2]) in ("void", "draft"):
            raise InvalidTransitionError(
                f"Cannot credit note invoice in status={inv[2]}"
            )
        if amount <= 0:
            raise ValidationError("amount must be > 0")
        inv_total = Decimal(str(inv[0]))
        if amount > inv_total:
            raise InsufficientFundsError(
                f"Credit note amount {amount} exceeds invoice total {inv_total}"
            )

        now = _now()
        cn_num = _generate_cn_number(self._conn)
        cnid = _next_id(self._conn, "app_credit_note")
        self._conn.execute(
            f"INSERT INTO app_credit_note ({_CN_COLS}) VALUES (?,?,?,?,?,?,?,'draft',NULL,NULL,?,?)",
            [cnid, organization_id, invoice_id, cn_num, str(amount),
             str(inv[1]), reason, now, now],
        )
        self._conn.execute(
            "UPDATE app_credit_note SET status='issued', issued_at=?, updated_at=? WHERE id=?",
            [now, now, cnid],
        )
        _audit(
            self._conn, action="credit_note.created",
            target_type="credit_note", target_id=str(cnid),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"amount": str(amount), "invoice_id": invoice_id},
            reason=reason,
            request_id=request_id,
        )
        row = self._conn.execute(
            f"SELECT {_CN_COLS} FROM app_credit_note WHERE id = ?", [cnid]
        ).fetchone()
        return _map_cn(row)

    def apply(
        self,
        credit_note_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        request_id: Optional[str] = None,
    ) -> CreditNote:
        cn_row = self._conn.execute(
            f"SELECT {_CN_COLS} FROM app_credit_note WHERE id = ? AND organization_id = ?",
            [credit_note_id, organization_id],
        ).fetchone()
        if not cn_row:
            raise NotFoundError(f"credit_note id={credit_note_id}")
        cn = _map_cn(cn_row)
        if cn.status != "issued":
            raise InvalidTransitionError(f"Credit note must be issued to apply (status={cn.status})")

        now = _now()
        self._conn.execute(
            "UPDATE app_credit_note SET status='applied', applied_at=?, updated_at=? WHERE id=?",
            [now, now, credit_note_id],
        )
        inv = self._conn.execute(
            "SELECT total, amount_paid, status FROM app_invoice WHERE id = ?", [cn.invoice_id]
        ).fetchone()
        if inv:
            inv_total = Decimal(str(inv[0]))
            inv_paid = Decimal(str(inv[1])) + cn.amount
            new_due = max(inv_total - inv_paid, Decimal("0"))
            new_status = "credited" if inv_paid >= inv_total else "partially_credited"
            self._conn.execute(
                "UPDATE app_invoice SET amount_paid=?, amount_due=?, status=?, updated_at=? WHERE id=?",
                [str(inv_paid), str(new_due), new_status, now, cn.invoice_id],
            )
        _append_ledger(
            self._conn,
            organization_id=organization_id,
            entry_type="credit_note_applied",
            reference_type="credit_note",
            reference_id=credit_note_id,
            amount=-cn.amount,
            currency=cn.currency,
            description=f"Credit note {cn.credit_note_number} applied",
        )
        _audit(
            self._conn, action="credit_note.applied",
            target_type="credit_note", target_id=str(credit_note_id),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"status": "applied"},
            request_id=request_id,
        )
        row = self._conn.execute(
            f"SELECT {_CN_COLS} FROM app_credit_note WHERE id = ?", [credit_note_id]
        ).fetchone()
        return _map_cn(row)

    def list(
        self,
        *,
        organization_id: int,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[CreditNote], int]:
        total = int(
            self._conn.execute(
                "SELECT COUNT(*) FROM app_credit_note WHERE organization_id = ?", [organization_id]
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_CN_COLS} FROM app_credit_note WHERE organization_id = ? "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            [organization_id, limit, offset],
        ).fetchall()
        return [_map_cn(r) for r in rows], total


# ── ProviderEvent Use Cases ────────────────────────────────────────────────────


class ProviderEventUseCases:
    """ProcessProviderEvent (idempotent)."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def process(
        self,
        *,
        provider_code: str,
        provider_event_id: str,
        event_type: str,
        payload: Optional[str] = None,
    ) -> PaymentProviderEvent:
        existing = self._conn.execute(
            f"SELECT {_EVENT_COLS} FROM app_payment_provider_event WHERE provider_event_id = ?",
            [provider_event_id],
        ).fetchone()
        if existing:
            return _map_event(existing)

        now = _now()
        eid = _next_id(self._conn, "app_payment_provider_event")
        self._conn.execute(
            f"""
            INSERT INTO app_payment_provider_event ({_EVENT_COLS})
            VALUES (?,?,?,?,?,TRUE,?,?)
            """,
            [eid, provider_code, provider_event_id, event_type, payload, now, now],
        )
        row = self._conn.execute(
            f"SELECT {_EVENT_COLS} FROM app_payment_provider_event WHERE id = ?", [eid]
        ).fetchone()
        return _map_event(row)

    def list(
        self,
        *,
        provider_code: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[PaymentProviderEvent], int]:
        conditions: list[str] = []
        params: list[Any] = []
        if provider_code:
            conditions.append("provider_code = ?")
            params.append(provider_code)
        where = " AND ".join(conditions) if conditions else "1=1"
        total = int(
            self._conn.execute(
                f"SELECT COUNT(*) FROM app_payment_provider_event WHERE {where}", params
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_EVENT_COLS} FROM app_payment_provider_event WHERE {where} "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [_map_event(r) for r in rows], total


# ── Ledger Use Cases ───────────────────────────────────────────────────────────


class LedgerUseCases:
    """List ledger entries. No write methods — append-only at lower levels."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def list(
        self,
        *,
        organization_id: int,
        entry_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[BillingLedgerEntry], int]:
        conditions = ["organization_id = ?"]
        params: list[Any] = [organization_id]
        if entry_type:
            conditions.append("entry_type = ?")
            params.append(entry_type)
        where = " AND ".join(conditions)
        total = int(
            self._conn.execute(
                f"SELECT COUNT(*) FROM app_billing_ledger_entry WHERE {where}", params
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_LEDGER_COLS} FROM app_billing_ledger_entry WHERE {where} "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [_map_ledger(r) for r in rows], total

    def update_guard(self) -> None:
        """Always raises LedgerImmutableError. Prevents accidental updates."""
        raise LedgerImmutableError("Ledger entries are append-only and cannot be updated")

    def delete_guard(self) -> None:
        """Always raises LedgerImmutableError. Prevents accidental deletes."""
        raise LedgerImmutableError("Ledger entries are append-only and cannot be deleted")
