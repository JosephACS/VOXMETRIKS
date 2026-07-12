"""CRM consolidated use cases — Spec 017.

Covers: Prospects, Contacts, Opportunities, Activities, Quotations,
        Approvals, Conversion.

CRM owns the workflow; contracts package owns app_commercial_contract.
Conversion path B calls organizations.CreateOrganization with signatory user as actor.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.crm.domain.entities import (
    ApprovalRequest,
    Contact,
    CustomerConversion,
    Opportunity,
    OpportunityStageHistory,
    Prospect,
    ProspectContact,
    QuotationItem,
    QuotationVersion,
    Quotation,
    SalesActivity,
)
from app.packages.crm.domain.errors import (
    ApprovalConflict,
    ApprovalRequiredError,
    ConflictError,
    ConversionConflict,
    ImmutableError,
    NotFoundError,
    PersistenceError,
    StaleDataError,
    TokenAlreadyUsedError,
    TokenExpiredError,
    ValidationError,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


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
    actor_platform_role: Optional[str] = None,
    organization_id: Optional[int] = None,
    previous_values: Optional[dict[str, Any]] = None,
    new_values: Optional[dict[str, Any]] = None,
    reason: Optional[str] = None,
    request_id: Optional[str] = None,
    result: str = "success",
) -> None:
    from app.packages.organizations.infrastructure.repositories.audit_repository import AuditRepository
    AuditRepository(conn).append(
        action=action,
        target_type=target_type,
        target_id=target_id,
        source="crm.use_case",
        result=result,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        actor_platform_role=actor_platform_role,
        previous_values=previous_values,
        new_values=new_values,
        reason=reason,
        request_id=request_id,
    )


# ── Prospect row mapper ───────────────────────────────────────────────────────

def _map_prospect(row: tuple) -> Prospect:
    return Prospect(
        id=int(row[0]),
        display_name=str(row[1]),
        company_name=row[2],
        email=row[3],
        phone=row[4],
        source=row[5],
        status=str(row[6]),
        owner_user_id=int(row[7]),
        organization_id=int(row[8]) if row[8] is not None else None,
        notes=row[9],
        created_at=row[10],
        updated_at=row[11],
        deleted_at=row[12],
    )


_PROSPECT_COLS = (
    "id, display_name, company_name, email, phone, source, status, "
    "owner_user_id, organization_id, notes, created_at, updated_at, deleted_at"
)


def _map_contact(row: tuple) -> Contact:
    return Contact(
        id=int(row[0]),
        full_name=str(row[1]),
        email=row[2],
        email_normalized=row[3],
        phone=row[4],
        company_name=row[5],
        linked_user_id=int(row[6]) if row[6] is not None else None,
        created_by=int(row[7]),
        created_at=row[8],
        updated_at=row[9],
        deleted_at=row[10],
    )


_CONTACT_COLS = (
    "id, full_name, email, email_normalized, phone, company_name, "
    "linked_user_id, created_by, created_at, updated_at, deleted_at"
)


def _map_opportunity(row: tuple) -> Opportunity:
    return Opportunity(
        id=int(row[0]),
        prospect_id=int(row[1]),
        name=str(row[2]),
        description=row[3],
        stage=str(row[4]),
        probability=int(row[5]) if row[5] is not None else 0,
        expected_value=Decimal(str(row[6])) if row[6] is not None else None,
        currency=row[7],
        expected_close_date=row[8],
        actual_close_date=row[9],
        outcome=row[10],
        owner_user_id=int(row[11]),
        organization_id=int(row[12]) if row[12] is not None else None,
        created_at=row[13],
        updated_at=row[14],
        deleted_at=row[15],
    )


_OPP_COLS = (
    "id, prospect_id, name, description, stage, probability, expected_value, currency, "
    "expected_close_date, actual_close_date, outcome, owner_user_id, organization_id, "
    "created_at, updated_at, deleted_at"
)


def _map_activity(row: tuple) -> SalesActivity:
    return SalesActivity(
        id=int(row[0]),
        activity_type=str(row[1]),
        subject=row[2],
        body=row[3],
        outcome=row[4],
        prospect_id=int(row[5]) if row[5] is not None else None,
        contact_id=int(row[6]) if row[6] is not None else None,
        opportunity_id=int(row[7]) if row[7] is not None else None,
        actor_user_id=int(row[8]),
        scheduled_at=row[9],
        completed_at=row[10],
        status=str(row[11]),
        created_at=row[12],
        updated_at=row[13],
        deleted_at=row[14],
    )


_ACTIVITY_COLS = (
    "id, activity_type, subject, body, outcome, prospect_id, contact_id, opportunity_id, "
    "actor_user_id, scheduled_at, completed_at, status, created_at, updated_at, deleted_at"
)


def _map_quotation(row: tuple) -> Quotation:
    return Quotation(
        id=int(row[0]),
        opportunity_id=int(row[1]),
        status=str(row[2]),
        currency=str(row[3]),
        notes=row[4],
        row_version=int(row[5]),
        current_version_no=int(row[6]),
        created_by=int(row[7]),
        created_at=row[8],
        updated_at=row[9],
        deleted_at=row[10],
    )


_QUOTATION_COLS = (
    "id, opportunity_id, status, currency, notes, row_version, current_version_no, "
    "created_by, created_at, updated_at, deleted_at"
)


def _map_quotation_version(row: tuple) -> QuotationVersion:
    return QuotationVersion(
        id=int(row[0]),
        quotation_id=int(row[1]),
        version_no=int(row[2]),
        status=str(row[3]),
        subtotal=Decimal(str(row[4])),
        discount_pct=Decimal(str(row[5])),
        discount_requires_approval=bool(row[6]),
        total=Decimal(str(row[7])),
        notes=row[8],
        sent_at=row[9],
        accepted_at=row[10],
        rejected_at=row[11],
        is_immutable=bool(row[12]),
        created_by=int(row[13]),
        created_at=row[14],
    )


_QV_COLS = (
    "id, quotation_id, version_no, status, subtotal, discount_pct, "
    "discount_requires_approval, total, notes, sent_at, accepted_at, rejected_at, "
    "is_immutable, created_by, created_at"
)


def _map_quotation_item(row: tuple) -> QuotationItem:
    return QuotationItem(
        id=int(row[0]),
        quotation_version_id=int(row[1]),
        description=str(row[2]),
        quantity=Decimal(str(row[3])),
        unit_price=Decimal(str(row[4])),
        discount_pct=Decimal(str(row[5])),
        line_total=Decimal(str(row[6])),
        plan_code=row[7],
        sort_order=int(row[8]),
        created_at=row[9],
    )


_QI_COLS = (
    "id, quotation_version_id, description, quantity, unit_price, discount_pct, "
    "line_total, plan_code, sort_order, created_at"
)


def _map_approval(row: tuple) -> ApprovalRequest:
    return ApprovalRequest(
        id=int(row[0]),
        object_type=str(row[1]),
        object_id=int(row[2]),
        reason=str(row[3]),
        threshold_ref=row[4],
        status=str(row[5]),
        requested_by=int(row[6]),
        reviewed_by=int(row[7]) if row[7] is not None else None,
        review_note=row[8],
        requested_at=row[9],
        reviewed_at=row[10],
        created_at=row[11],
        updated_at=row[12],
    )


_APPROVAL_COLS = (
    "id, object_type, object_id, reason, threshold_ref, status, "
    "requested_by, reviewed_by, review_note, requested_at, reviewed_at, "
    "created_at, updated_at"
)


def _map_conversion(row: tuple) -> CustomerConversion:
    return CustomerConversion(
        id=int(row[0]),
        opportunity_id=int(row[1]),
        mode=str(row[2]),
        status=str(row[3]),
        organization_id=int(row[4]) if row[4] is not None else None,
        contact_id=int(row[5]) if row[5] is not None else None,
        signatory_user_id=int(row[6]) if row[6] is not None else None,
        claim_token_hash=row[7],
        claim_token_expires_at=row[8],
        claim_consumed_at=row[9],
        idempotency_key=row[10],
        requested_by=int(row[11]),
        completed_at=row[12],
        failure_reason=row[13],
        created_at=row[14],
        updated_at=row[15],
    )


_CONV_COLS = (
    "id, opportunity_id, mode, status, organization_id, contact_id, "
    "signatory_user_id, claim_token_hash, claim_token_expires_at, claim_consumed_at, "
    "idempotency_key, requested_by, completed_at, failure_reason, created_at, updated_at"
)


# ── Prospect Use Cases ────────────────────────────────────────────────────────

class ProspectUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        display_name: str,
        company_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        source: Optional[str] = None,
        notes: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Prospect:
        if not display_name or not display_name.strip():
            raise ValidationError("display_name is required")

        now = _now()
        pid = _next_id(self._conn, "app_crm_prospect")
        self._conn.execute(
            f"""
            INSERT INTO app_crm_prospect
                ({_PROSPECT_COLS})
            VALUES (?, ?, ?, ?, ?, ?, 'new', ?, NULL, ?, ?, ?, NULL)
            """,
            [pid, display_name.strip(), company_name, email, phone, source,
             actor_user_id, notes, now, now],
        )
        prospect = self._get_or_raise(pid)
        _audit(
            self._conn,
            action="crm.prospect.created",
            target_type="crm_prospect",
            target_id=str(pid),
            actor_user_id=actor_user_id,
            new_values={"display_name": prospect.display_name, "status": prospect.status},
            request_id=request_id,
        )
        return prospect

    def get(self, prospect_id: int) -> Prospect:
        return self._get_or_raise(prospect_id)

    def list(
        self,
        *,
        owner_user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[Prospect], int]:
        conditions = ["deleted_at IS NULL"]
        params: list[Any] = []
        if owner_user_id is not None:
            conditions.append("owner_user_id = ?")
            params.append(owner_user_id)
        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        where = " AND ".join(conditions)

        total = int(
            self._conn.execute(
                f"SELECT COUNT(*) FROM app_crm_prospect WHERE {where}", params
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_PROSPECT_COLS} FROM app_crm_prospect WHERE {where} "
            f"ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [_map_prospect(r) for r in rows], total

    def update(
        self,
        prospect_id: int,
        *,
        actor_user_id: int,
        display_name: Optional[str] = None,
        company_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        source: Optional[str] = None,
        notes: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Prospect:
        existing = self._get_or_raise(prospect_id)
        now = _now()
        self._conn.execute(
            """
            UPDATE app_crm_prospect SET
                display_name = COALESCE(?, display_name),
                company_name = COALESCE(?, company_name),
                email = COALESCE(?, email),
                phone = COALESCE(?, phone),
                source = COALESCE(?, source),
                notes = COALESCE(?, notes),
                updated_at = ?
            WHERE id = ? AND deleted_at IS NULL
            """,
            [display_name, company_name, email, phone, source, notes, now, prospect_id],
        )
        updated = self._get_or_raise(prospect_id)
        _audit(
            self._conn,
            action="crm.prospect.updated",
            target_type="crm_prospect",
            target_id=str(prospect_id),
            actor_user_id=actor_user_id,
            previous_values={"display_name": existing.display_name},
            new_values={"display_name": updated.display_name},
            request_id=request_id,
        )
        return updated

    def transition_status(
        self,
        prospect_id: int,
        *,
        actor_user_id: int,
        new_status: str,
        request_id: Optional[str] = None,
    ) -> Prospect:
        valid_statuses = {"contacted", "qualified", "disqualified", "lost"}
        if new_status not in valid_statuses:
            raise ValidationError(f"Invalid status transition: {new_status}")
        existing = self._get_or_raise(prospect_id)
        if existing.status in ("converted",):
            raise ValidationError(f"Cannot transition from {existing.status}")
        now = _now()
        self._conn.execute(
            "UPDATE app_crm_prospect SET status = ?, updated_at = ? WHERE id = ?",
            [new_status, now, prospect_id],
        )
        updated = self._get_or_raise(prospect_id)
        _audit(
            self._conn,
            action="crm.prospect.status_changed",
            target_type="crm_prospect",
            target_id=str(prospect_id),
            actor_user_id=actor_user_id,
            previous_values={"status": existing.status},
            new_values={"status": new_status},
            request_id=request_id,
        )
        return updated

    def soft_delete(self, prospect_id: int, *, actor_user_id: int) -> Prospect:
        existing = self._get_or_raise(prospect_id)
        now = _now()
        self._conn.execute(
            "UPDATE app_crm_prospect SET deleted_at = ?, updated_at = ? WHERE id = ?",
            [now, now, prospect_id],
        )
        _audit(
            self._conn,
            action="crm.prospect.deleted",
            target_type="crm_prospect",
            target_id=str(prospect_id),
            actor_user_id=actor_user_id,
            previous_values={"status": existing.status},
            new_values={"deleted": True},
        )
        return self._get_or_raise(prospect_id)

    def _get_or_raise(self, prospect_id: int) -> Prospect:
        row = self._conn.execute(
            f"SELECT {_PROSPECT_COLS} FROM app_crm_prospect WHERE id = ?",
            [prospect_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"prospect id={prospect_id}")
        return _map_prospect(row)


# ── Contact Use Cases ─────────────────────────────────────────────────────────

class ContactUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        full_name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company_name: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Contact:
        if not full_name or not full_name.strip():
            raise ValidationError("full_name is required")
        email_norm = email.strip().lower() if email else None
        now = _now()
        cid = _next_id(self._conn, "app_crm_contact")
        self._conn.execute(
            f"""
            INSERT INTO app_crm_contact
                ({_CONTACT_COLS})
            VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, NULL)
            """,
            [cid, full_name.strip(), email, email_norm, phone, company_name,
             actor_user_id, now, now],
        )
        contact = self._get_or_raise(cid)
        _audit(
            self._conn,
            action="crm.contact.created",
            target_type="crm_contact",
            target_id=str(cid),
            actor_user_id=actor_user_id,
            new_values={"full_name": contact.full_name},
            request_id=request_id,
        )
        return contact

    def get(self, contact_id: int) -> Contact:
        return self._get_or_raise(contact_id)

    def list(
        self,
        *,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[Contact], int]:
        total = int(
            self._conn.execute(
                "SELECT COUNT(*) FROM app_crm_contact WHERE deleted_at IS NULL"
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_CONTACT_COLS} FROM app_crm_contact WHERE deleted_at IS NULL "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            [limit, offset],
        ).fetchall()
        return [_map_contact(r) for r in rows], total

    def update(
        self,
        contact_id: int,
        *,
        actor_user_id: int,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company_name: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Contact:
        self._get_or_raise(contact_id)
        email_norm = email.strip().lower() if email else None
        now = _now()
        self._conn.execute(
            """
            UPDATE app_crm_contact SET
                full_name = COALESCE(?, full_name),
                email = COALESCE(?, email),
                email_normalized = COALESCE(?, email_normalized),
                phone = COALESCE(?, phone),
                company_name = COALESCE(?, company_name),
                updated_at = ?
            WHERE id = ? AND deleted_at IS NULL
            """,
            [full_name, email, email_norm, phone, company_name, now, contact_id],
        )
        updated = self._get_or_raise(contact_id)
        _audit(
            self._conn,
            action="crm.contact.updated",
            target_type="crm_contact",
            target_id=str(contact_id),
            actor_user_id=actor_user_id,
            new_values={"full_name": updated.full_name},
            request_id=request_id,
        )
        return updated

    def link_to_prospect(
        self,
        *,
        prospect_id: int,
        contact_id: int,
        actor_user_id: int,
        is_primary: bool = False,
        is_decision_maker: bool = False,
        is_signatory: bool = False,
    ) -> ProspectContact:
        existing = self._conn.execute(
            "SELECT 1 FROM app_crm_prospect_contact WHERE prospect_id = ? AND contact_id = ?",
            [prospect_id, contact_id],
        ).fetchone()
        now = _now()
        if existing:
            self._conn.execute(
                """
                UPDATE app_crm_prospect_contact
                SET is_primary = ?, is_decision_maker = ?, is_signatory = ?, added_at = ?
                WHERE prospect_id = ? AND contact_id = ?
                """,
                [is_primary, is_decision_maker, is_signatory, now, prospect_id, contact_id],
            )
        else:
            self._conn.execute(
                """
                INSERT INTO app_crm_prospect_contact
                    (prospect_id, contact_id, is_primary, is_decision_maker, is_signatory, added_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [prospect_id, contact_id, is_primary, is_decision_maker, is_signatory, now],
            )
        row = self._conn.execute(
            "SELECT prospect_id, contact_id, is_primary, is_decision_maker, is_signatory, added_at "
            "FROM app_crm_prospect_contact WHERE prospect_id = ? AND contact_id = ?",
            [prospect_id, contact_id],
        ).fetchone()
        return ProspectContact(
            prospect_id=int(row[0]),
            contact_id=int(row[1]),
            is_primary=bool(row[2]),
            is_decision_maker=bool(row[3]),
            is_signatory=bool(row[4]),
            added_at=row[5],
        )

    def _get_or_raise(self, contact_id: int) -> Contact:
        row = self._conn.execute(
            f"SELECT {_CONTACT_COLS} FROM app_crm_contact WHERE id = ? AND deleted_at IS NULL",
            [contact_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"contact id={contact_id}")
        return _map_contact(row)


# ── Opportunity Use Cases ─────────────────────────────────────────────────────

_VALID_STAGE_TRANSITIONS: dict[str, set[str]] = {
    "qualification": {"proposal", "closed_lost", "canceled"},
    "proposal": {"negotiation", "closed_won", "closed_lost", "canceled"},
    "negotiation": {"closed_won", "closed_lost", "canceled"},
    "closed_won": set(),
    "closed_lost": set(),
    "canceled": set(),
}


class OpportunityUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        prospect_id: int,
        name: str,
        description: Optional[str] = None,
        expected_value: Optional[Decimal] = None,
        currency: Optional[str] = None,
        probability: int = 0,
        expected_close_date=None,
        request_id: Optional[str] = None,
    ) -> Opportunity:
        if not name or not name.strip():
            raise ValidationError("name is required")
        if probability < 0 or probability > 100:
            raise ValidationError("probability must be 0-100")

        now = _now()
        oid = _next_id(self._conn, "app_crm_opportunity")
        self._conn.execute(
            f"""
            INSERT INTO app_crm_opportunity
                ({_OPP_COLS})
            VALUES (?, ?, ?, ?, 'qualification', ?, ?, ?, ?, NULL, NULL, ?, NULL, ?, ?, NULL)
            """,
            [oid, prospect_id, name.strip(), description, probability,
             str(expected_value) if expected_value else None,
             currency, expected_close_date,
             actor_user_id, now, now],
        )
        opp = self._get_or_raise(oid)
        self._append_stage_history(opp, from_stage=None, to_stage="qualification", actor_user_id=actor_user_id)
        _audit(
            self._conn,
            action="crm.opportunity.created",
            target_type="crm_opportunity",
            target_id=str(oid),
            actor_user_id=actor_user_id,
            new_values={"name": opp.name, "stage": opp.stage},
            request_id=request_id,
        )
        return opp

    def get(self, opportunity_id: int) -> Opportunity:
        return self._get_or_raise(opportunity_id)

    def list(
        self,
        *,
        owner_user_id: Optional[int] = None,
        stage: Optional[str] = None,
        prospect_id: Optional[int] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[Opportunity], int]:
        conditions = ["deleted_at IS NULL"]
        params: list[Any] = []
        if owner_user_id is not None:
            conditions.append("owner_user_id = ?")
            params.append(owner_user_id)
        if stage is not None:
            conditions.append("stage = ?")
            params.append(stage)
        if prospect_id is not None:
            conditions.append("prospect_id = ?")
            params.append(prospect_id)
        where = " AND ".join(conditions)

        total = int(
            self._conn.execute(
                f"SELECT COUNT(*) FROM app_crm_opportunity WHERE {where}", params
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_OPP_COLS} FROM app_crm_opportunity WHERE {where} "
            f"ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [_map_opportunity(r) for r in rows], total

    def update(
        self,
        opportunity_id: int,
        *,
        actor_user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        expected_value: Optional[Decimal] = None,
        currency: Optional[str] = None,
        probability: Optional[int] = None,
        expected_close_date=None,
        request_id: Optional[str] = None,
    ) -> Opportunity:
        existing = self._get_or_raise(opportunity_id)
        if existing.stage in ("closed_won", "closed_lost", "canceled"):
            raise ValidationError(f"Cannot update closed opportunity (stage={existing.stage})")
        if probability is not None and (probability < 0 or probability > 100):
            raise ValidationError("probability must be 0-100")
        now = _now()
        self._conn.execute(
            """
            UPDATE app_crm_opportunity SET
                name = COALESCE(?, name),
                description = COALESCE(?, description),
                expected_value = COALESCE(?, expected_value),
                currency = COALESCE(?, currency),
                probability = COALESCE(?, probability),
                expected_close_date = COALESCE(?, expected_close_date),
                updated_at = ?
            WHERE id = ?
            """,
            [name, description,
             str(expected_value) if expected_value is not None else None,
             currency, probability, expected_close_date, now, opportunity_id],
        )
        updated = self._get_or_raise(opportunity_id)
        _audit(
            self._conn,
            action="crm.opportunity.updated",
            target_type="crm_opportunity",
            target_id=str(opportunity_id),
            actor_user_id=actor_user_id,
            previous_values={"name": existing.name, "stage": existing.stage},
            new_values={"name": updated.name},
            request_id=request_id,
        )
        return updated

    def advance_stage(
        self,
        opportunity_id: int,
        *,
        actor_user_id: int,
        new_stage: str,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Opportunity:
        opp = self._get_or_raise(opportunity_id)
        allowed = _VALID_STAGE_TRANSITIONS.get(opp.stage, set())
        if new_stage not in allowed:
            raise ValidationError(
                f"Cannot transition opportunity from {opp.stage!r} to {new_stage!r}"
            )
        now = _now()
        self._conn.execute(
            "UPDATE app_crm_opportunity SET stage = ?, updated_at = ? WHERE id = ?",
            [new_stage, now, opportunity_id],
        )
        updated = self._get_or_raise(opportunity_id)
        self._append_stage_history(updated, from_stage=opp.stage, to_stage=new_stage, actor_user_id=actor_user_id, reason=reason)
        _audit(
            self._conn,
            action="crm.opportunity.stage_changed",
            target_type="crm_opportunity",
            target_id=str(opportunity_id),
            actor_user_id=actor_user_id,
            previous_values={"stage": opp.stage},
            new_values={"stage": new_stage},
            reason=reason,
            request_id=request_id,
        )
        return updated

    def close(
        self,
        opportunity_id: int,
        *,
        actor_user_id: int,
        outcome: str,
        new_stage: str,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Opportunity:
        if new_stage not in ("closed_won", "closed_lost", "canceled"):
            raise ValidationError("close stage must be closed_won, closed_lost, or canceled")
        opp = self._get_or_raise(opportunity_id)
        if opp.stage in ("closed_won", "closed_lost", "canceled"):
            raise ValidationError(f"Opportunity already closed (stage={opp.stage})")
        now = _now()
        self._conn.execute(
            """
            UPDATE app_crm_opportunity SET
                stage = ?, outcome = ?, actual_close_date = ?, updated_at = ?
            WHERE id = ?
            """,
            [new_stage, outcome, now.date(), now, opportunity_id],
        )
        updated = self._get_or_raise(opportunity_id)
        self._append_stage_history(updated, from_stage=opp.stage, to_stage=new_stage, actor_user_id=actor_user_id, reason=reason)
        _audit(
            self._conn,
            action="crm.opportunity.closed",
            target_type="crm_opportunity",
            target_id=str(opportunity_id),
            actor_user_id=actor_user_id,
            previous_values={"stage": opp.stage},
            new_values={"stage": new_stage, "outcome": outcome},
            reason=reason,
            request_id=request_id,
        )
        return updated

    def stage_history(self, opportunity_id: int) -> list[OpportunityStageHistory]:
        rows = self._conn.execute(
            "SELECT id, opportunity_id, from_stage, to_stage, actor_user_id, reason, occurred_at "
            "FROM app_crm_opportunity_stage_history WHERE opportunity_id = ? ORDER BY occurred_at ASC",
            [opportunity_id],
        ).fetchall()
        return [
            OpportunityStageHistory(
                id=int(r[0]), opportunity_id=int(r[1]), from_stage=r[2],
                to_stage=str(r[3]), actor_user_id=int(r[4]), reason=r[5], occurred_at=r[6],
            )
            for r in rows
        ]

    def _append_stage_history(
        self,
        opp: Opportunity,
        *,
        from_stage: Optional[str],
        to_stage: str,
        actor_user_id: int,
        reason: Optional[str] = None,
    ) -> None:
        hid = _next_id(self._conn, "app_crm_opportunity_stage_history")
        self._conn.execute(
            """
            INSERT INTO app_crm_opportunity_stage_history
                (id, opportunity_id, from_stage, to_stage, actor_user_id, reason, occurred_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [hid, opp.id, from_stage, to_stage, actor_user_id, reason, _now()],
        )

    def _get_or_raise(self, opportunity_id: int) -> Opportunity:
        row = self._conn.execute(
            f"SELECT {_OPP_COLS} FROM app_crm_opportunity WHERE id = ? AND deleted_at IS NULL",
            [opportunity_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"opportunity id={opportunity_id}")
        return _map_opportunity(row)


# ── Activity Use Cases ────────────────────────────────────────────────────────

class ActivityUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        activity_type: str,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        prospect_id: Optional[int] = None,
        contact_id: Optional[int] = None,
        opportunity_id: Optional[int] = None,
        scheduled_at: Optional[datetime] = None,
        request_id: Optional[str] = None,
    ) -> SalesActivity:
        valid_types = {"call", "email", "meeting", "note", "demo", "other"}
        if activity_type not in valid_types:
            raise ValidationError(f"Invalid activity_type: {activity_type}")
        if prospect_id is None and contact_id is None and opportunity_id is None:
            raise ValidationError("At least one of prospect_id, contact_id, opportunity_id is required")

        now = _now()
        aid = _next_id(self._conn, "app_crm_sales_activity")
        self._conn.execute(
            f"""
            INSERT INTO app_crm_sales_activity
                ({_ACTIVITY_COLS})
            VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, NULL, 'planned', ?, ?, NULL)
            """,
            [aid, activity_type, subject, body,
             prospect_id, contact_id, opportunity_id,
             actor_user_id, scheduled_at, now, now],
        )
        act = self._get_or_raise(aid)
        _audit(
            self._conn,
            action="crm.activity.created",
            target_type="crm_sales_activity",
            target_id=str(aid),
            actor_user_id=actor_user_id,
            new_values={"activity_type": activity_type},
            request_id=request_id,
        )
        return act

    def get(self, activity_id: int) -> SalesActivity:
        return self._get_or_raise(activity_id)

    def list(
        self,
        *,
        opportunity_id: Optional[int] = None,
        prospect_id: Optional[int] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[SalesActivity], int]:
        conditions = ["deleted_at IS NULL"]
        params: list[Any] = []
        if opportunity_id is not None:
            conditions.append("opportunity_id = ?")
            params.append(opportunity_id)
        if prospect_id is not None:
            conditions.append("prospect_id = ?")
            params.append(prospect_id)
        where = " AND ".join(conditions)
        total = int(
            self._conn.execute(
                f"SELECT COUNT(*) FROM app_crm_sales_activity WHERE {where}", params
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_ACTIVITY_COLS} FROM app_crm_sales_activity WHERE {where} "
            f"ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [_map_activity(r) for r in rows], total

    def update(
        self,
        activity_id: int,
        *,
        actor_user_id: int,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        outcome: Optional[str] = None,
        status: Optional[str] = None,
        completed_at: Optional[datetime] = None,
        request_id: Optional[str] = None,
    ) -> SalesActivity:
        existing = self._get_or_raise(activity_id)
        if existing.status == "canceled":
            raise ValidationError("Cannot update a canceled activity")
        if status and status not in {"planned", "completed", "canceled"}:
            raise ValidationError(f"Invalid status: {status}")
        now = _now()
        self._conn.execute(
            """
            UPDATE app_crm_sales_activity SET
                subject = COALESCE(?, subject),
                body = COALESCE(?, body),
                outcome = COALESCE(?, outcome),
                status = COALESCE(?, status),
                completed_at = COALESCE(?, completed_at),
                updated_at = ?
            WHERE id = ?
            """,
            [subject, body, outcome, status, completed_at, now, activity_id],
        )
        updated = self._get_or_raise(activity_id)
        _audit(
            self._conn,
            action="crm.activity.updated",
            target_type="crm_sales_activity",
            target_id=str(activity_id),
            actor_user_id=actor_user_id,
            previous_values={"status": existing.status},
            new_values={"status": updated.status},
            request_id=request_id,
        )
        return updated

    def _get_or_raise(self, activity_id: int) -> SalesActivity:
        row = self._conn.execute(
            f"SELECT {_ACTIVITY_COLS} FROM app_crm_sales_activity WHERE id = ? AND deleted_at IS NULL",
            [activity_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"activity id={activity_id}")
        return _map_activity(row)


# ── Quotation Use Cases ───────────────────────────────────────────────────────

class QuotationUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        opportunity_id: int,
        currency: str,
        notes: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Quotation:
        if not currency or len(currency.strip()) != 3:
            raise ValidationError("currency must be a 3-char ISO code")
        now = _now()
        qid = _next_id(self._conn, "app_crm_quotation")
        self._conn.execute(
            f"""
            INSERT INTO app_crm_quotation
                ({_QUOTATION_COLS})
            VALUES (?, ?, 'draft', ?, ?, 1, 0, ?, ?, ?, NULL)
            """,
            [qid, opportunity_id, currency.strip().upper(), notes, actor_user_id, now, now],
        )
        q = self._get_or_raise(qid)
        _audit(
            self._conn,
            action="crm.quotation.created",
            target_type="crm_quotation",
            target_id=str(qid),
            actor_user_id=actor_user_id,
            new_values={"opportunity_id": opportunity_id, "currency": currency},
            request_id=request_id,
        )
        return q

    def get(self, quotation_id: int) -> Quotation:
        return self._get_or_raise(quotation_id)

    def list(
        self,
        *,
        opportunity_id: Optional[int] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[Quotation], int]:
        conditions = ["deleted_at IS NULL"]
        params: list[Any] = []
        if opportunity_id is not None:
            conditions.append("opportunity_id = ?")
            params.append(opportunity_id)
        where = " AND ".join(conditions)
        total = int(
            self._conn.execute(
                f"SELECT COUNT(*) FROM app_crm_quotation WHERE {where}", params
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_QUOTATION_COLS} FROM app_crm_quotation WHERE {where} "
            f"ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [_map_quotation(r) for r in rows], total

    # ── Version management ────────────────────────────────────────────────────

    def create_version(
        self,
        quotation_id: int,
        *,
        actor_user_id: int,
        notes: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> QuotationVersion:
        q = self._get_or_raise(quotation_id)
        if q.status in ("accepted",):
            raise ValidationError("Cannot create version for accepted quotation")
        now = _now()
        next_version_no = q.current_version_no + 1
        vid = _next_id(self._conn, "app_crm_quotation_version")
        self._conn.execute(
            f"""
            INSERT INTO app_crm_quotation_version
                ({_QV_COLS})
            VALUES (?, ?, ?, 'draft', 0, 0, FALSE, 0, ?, NULL, NULL, NULL, FALSE, ?, ?)
            """,
            [vid, quotation_id, next_version_no, notes, actor_user_id, now],
        )
        self._conn.execute(
            """
            UPDATE app_crm_quotation
            SET current_version_no = ?, row_version = row_version + 1, updated_at = ?
            WHERE id = ?
            """,
            [next_version_no, now, quotation_id],
        )
        version = self._get_version_or_raise(vid)
        _audit(
            self._conn,
            action="crm.quotation.version_created",
            target_type="crm_quotation_version",
            target_id=str(vid),
            actor_user_id=actor_user_id,
            new_values={"quotation_id": quotation_id, "version_no": next_version_no},
            request_id=request_id,
        )
        return version

    def get_version(self, version_id: int) -> QuotationVersion:
        return self._get_version_or_raise(version_id)

    def list_versions(self, quotation_id: int) -> list[QuotationVersion]:
        rows = self._conn.execute(
            f"SELECT {_QV_COLS} FROM app_crm_quotation_version WHERE quotation_id = ? ORDER BY version_no ASC",
            [quotation_id],
        ).fetchall()
        return [_map_quotation_version(r) for r in rows]

    def add_item(
        self,
        version_id: int,
        *,
        actor_user_id: int,
        description: str,
        quantity: Decimal,
        unit_price: Decimal,
        discount_pct: Decimal = Decimal("0"),
        plan_code: Optional[str] = None,
        sort_order: int = 0,
        request_id: Optional[str] = None,
    ) -> QuotationItem:
        version = self._get_version_or_raise(version_id)
        if version.is_immutable:
            raise ImmutableError("Cannot modify a sent quotation version")
        if version.status not in ("draft", "pending_approval"):
            raise ImmutableError(f"Cannot add items to version in status={version.status}")

        line_total = quantity * unit_price * (1 - discount_pct / 100)
        now = _now()
        iid = _next_id(self._conn, "app_crm_quotation_item")
        self._conn.execute(
            f"""
            INSERT INTO app_crm_quotation_item
                ({_QI_COLS})
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [iid, version_id, description, str(quantity), str(unit_price),
             str(discount_pct), str(line_total), plan_code, sort_order, now],
        )
        self._recalculate_version_totals(version_id)
        item = self._conn.execute(
            f"SELECT {_QI_COLS} FROM app_crm_quotation_item WHERE id = ?", [iid]
        ).fetchone()
        return _map_quotation_item(item)

    def list_items(self, version_id: int) -> list[QuotationItem]:
        rows = self._conn.execute(
            f"SELECT {_QI_COLS} FROM app_crm_quotation_item WHERE quotation_version_id = ? ORDER BY sort_order ASC",
            [version_id],
        ).fetchall()
        return [_map_quotation_item(r) for r in rows]

    def send_version(
        self,
        version_id: int,
        *,
        actor_user_id: int,
        discount_approval_threshold: Optional[float] = None,
        request_id: Optional[str] = None,
    ) -> QuotationVersion:
        """Mark a quotation version as sent. Checks discount approval requirements.

        If no threshold configured, any discount > 0 requires manager approval first.
        If threshold configured, discount_pct > threshold requires approval.
        """
        version = self._get_version_or_raise(version_id)
        if version.is_immutable or version.status == "sent":
            raise ImmutableError("Version is already sent and immutable")
        if version.status == "pending_approval":
            raise ApprovalRequiredError("Version requires approval before sending")

        # Check header-level AND item-level discounts
        header_discount = float(version.discount_pct)
        item_discount_row = self._conn.execute(
            "SELECT COALESCE(MAX(discount_pct), 0) FROM app_crm_quotation_item WHERE quotation_version_id = ?",
            [version_id],
        ).fetchone()
        max_item_discount = float(item_discount_row[0]) if item_discount_row else 0.0
        effective_discount = max(header_discount, max_item_discount)

        if effective_discount > 0:
            if discount_approval_threshold is None:
                raise ApprovalRequiredError(
                    "Any discount > 0 requires manager approval when no threshold is configured"
                )
            if effective_discount > discount_approval_threshold:
                raise ApprovalRequiredError(
                    f"Discount {effective_discount}% exceeds threshold {discount_approval_threshold}%; approval required"
                )

        now = _now()
        self._conn.execute(
            """
            UPDATE app_crm_quotation_version
            SET status = 'sent', is_immutable = TRUE, sent_at = ?
            WHERE id = ?
            """,
            [now, version_id],
        )
        qid = version.quotation_id
        self._conn.execute(
            "UPDATE app_crm_quotation SET status = 'sent', updated_at = ? WHERE id = ?",
            [now, qid],
        )
        updated = self._get_version_or_raise(version_id)
        _audit(
            self._conn,
            action="crm.quotation.version_sent",
            target_type="crm_quotation_version",
            target_id=str(version_id),
            actor_user_id=actor_user_id,
            previous_values={"status": version.status},
            new_values={"status": "sent", "is_immutable": True},
            request_id=request_id,
        )
        return updated

    def request_discount_approval(
        self,
        version_id: int,
        *,
        actor_user_id: int,
        reason: str,
        request_id: Optional[str] = None,
    ) -> ApprovalRequest:
        version = self._get_version_or_raise(version_id)
        if version.is_immutable:
            raise ImmutableError("Cannot request approval for an immutable version")

        pending = self._conn.execute(
            "SELECT 1 FROM app_crm_approval_request "
            "WHERE object_type = 'quotation_version' AND object_id = ? AND status = 'pending'",
            [version_id],
        ).fetchone()
        if pending:
            raise ApprovalConflict("There is already a pending approval for this version")

        now = _now()
        self._conn.execute(
            "UPDATE app_crm_quotation_version SET status = 'pending_approval', discount_requires_approval = TRUE WHERE id = ?",
            [version_id],
        )
        arid = _next_id(self._conn, "app_crm_approval_request")
        self._conn.execute(
            f"""
            INSERT INTO app_crm_approval_request
                ({_APPROVAL_COLS})
            VALUES (?, 'quotation_version', ?, ?, NULL, 'pending', ?, NULL, NULL, ?, NULL, ?, ?)
            """,
            [arid, version_id, reason, actor_user_id, now, now, now],
        )
        _audit(
            self._conn,
            action="crm.approval.requested",
            target_type="crm_approval_request",
            target_id=str(arid),
            actor_user_id=actor_user_id,
            new_values={"object_type": "quotation_version", "object_id": version_id, "reason": reason},
            request_id=request_id,
        )
        return self._get_approval_or_raise(arid)

    def _recalculate_version_totals(self, version_id: int) -> None:
        row = self._conn.execute(
            """
            SELECT COALESCE(SUM(line_total), 0), COUNT(*)
            FROM app_crm_quotation_item WHERE quotation_version_id = ?
            """,
            [version_id],
        ).fetchone()
        subtotal = Decimal(str(row[0]))
        version = self._get_version_or_raise(version_id)
        discount_amount = subtotal * version.discount_pct / 100
        total = subtotal - discount_amount
        self._conn.execute(
            "UPDATE app_crm_quotation_version SET subtotal = ?, total = ? WHERE id = ?",
            [str(subtotal), str(total), version_id],
        )

    def _get_or_raise(self, quotation_id: int) -> Quotation:
        row = self._conn.execute(
            f"SELECT {_QUOTATION_COLS} FROM app_crm_quotation WHERE id = ? AND deleted_at IS NULL",
            [quotation_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"quotation id={quotation_id}")
        return _map_quotation(row)

    def _get_version_or_raise(self, version_id: int) -> QuotationVersion:
        row = self._conn.execute(
            f"SELECT {_QV_COLS} FROM app_crm_quotation_version WHERE id = ?",
            [version_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"quotation_version id={version_id}")
        return _map_quotation_version(row)

    def _get_approval_or_raise(self, approval_id: int) -> ApprovalRequest:
        row = self._conn.execute(
            f"SELECT {_APPROVAL_COLS} FROM app_crm_approval_request WHERE id = ?",
            [approval_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"approval id={approval_id}")
        return _map_approval(row)


# ── Approval Use Cases ────────────────────────────────────────────────────────

class ApprovalUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def get(self, approval_id: int) -> ApprovalRequest:
        return self._get_or_raise(approval_id)

    def list_pending(
        self,
        *,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[ApprovalRequest], int]:
        total = int(
            self._conn.execute(
                "SELECT COUNT(*) FROM app_crm_approval_request WHERE status = 'pending'"
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_APPROVAL_COLS} FROM app_crm_approval_request WHERE status = 'pending' "
            f"ORDER BY requested_at ASC LIMIT ? OFFSET ?",
            [limit, offset],
        ).fetchall()
        return [_map_approval(r) for r in rows], total

    def approve(
        self,
        approval_id: int,
        *,
        actor_user_id: int,
        review_note: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> ApprovalRequest:
        ar = self._get_or_raise(approval_id)
        if ar.status != "pending":
            raise ApprovalConflict(f"Approval is not pending (status={ar.status})")
        now = _now()
        self._conn.execute(
            """
            UPDATE app_crm_approval_request
            SET status = 'approved', reviewed_by = ?, review_note = ?, reviewed_at = ?, updated_at = ?
            WHERE id = ?
            """,
            [actor_user_id, review_note, now, now, approval_id],
        )
        if ar.object_type == "quotation_version":
            self._conn.execute(
                "UPDATE app_crm_quotation_version SET status = 'approved' WHERE id = ?",
                [ar.object_id],
            )
        updated = self._get_or_raise(approval_id)
        _audit(
            self._conn,
            action="crm.approval.approved",
            target_type="crm_approval_request",
            target_id=str(approval_id),
            actor_user_id=actor_user_id,
            previous_values={"status": ar.status},
            new_values={"status": "approved"},
            request_id=request_id,
        )
        return updated

    def reject(
        self,
        approval_id: int,
        *,
        actor_user_id: int,
        review_note: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> ApprovalRequest:
        ar = self._get_or_raise(approval_id)
        if ar.status != "pending":
            raise ApprovalConflict(f"Approval is not pending (status={ar.status})")
        now = _now()
        self._conn.execute(
            """
            UPDATE app_crm_approval_request
            SET status = 'rejected', reviewed_by = ?, review_note = ?, reviewed_at = ?, updated_at = ?
            WHERE id = ?
            """,
            [actor_user_id, review_note, now, now, approval_id],
        )
        if ar.object_type == "quotation_version":
            self._conn.execute(
                "UPDATE app_crm_quotation_version SET status = 'draft' WHERE id = ?",
                [ar.object_id],
            )
        updated = self._get_or_raise(approval_id)
        _audit(
            self._conn,
            action="crm.approval.rejected",
            target_type="crm_approval_request",
            target_id=str(approval_id),
            actor_user_id=actor_user_id,
            previous_values={"status": ar.status},
            new_values={"status": "rejected"},
            request_id=request_id,
        )
        return updated

    def _get_or_raise(self, approval_id: int) -> ApprovalRequest:
        row = self._conn.execute(
            f"SELECT {_APPROVAL_COLS} FROM app_crm_approval_request WHERE id = ?",
            [approval_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"approval id={approval_id}")
        return _map_approval(row)


# ── Conversion Use Cases ──────────────────────────────────────────────────────

_CLAIM_TOKEN_TTL_HOURS = 48


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class ConversionUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def prepare(
        self,
        *,
        actor_user_id: int,
        opportunity_id: int,
        mode: str,
        contact_id: Optional[int] = None,
        idempotency_key: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> tuple[CustomerConversion, Optional[str]]:
        """Prepare a conversion.

        Path A (link_existing): status stays 'pending'; org owner must confirm later.
        Path B (create_org): status becomes 'awaiting_customer_claim'; raw token returned ONCE.
        Returns (conversion, raw_token_or_None).
        """
        if mode not in ("create_org", "link_existing"):
            raise ValidationError("mode must be create_org or link_existing")

        # No double-conversion: check for completed conversion on this opportunity
        completed = self._conn.execute(
            "SELECT 1 FROM app_crm_customer_conversion "
            "WHERE opportunity_id = ? AND status = 'completed'",
            [opportunity_id],
        ).fetchone()
        if completed:
            raise ConversionConflict(f"Opportunity {opportunity_id} already has a completed conversion")

        # Idempotency check
        if idempotency_key:
            existing = self._conn.execute(
                "SELECT id FROM app_crm_customer_conversion WHERE idempotency_key = ?",
                [idempotency_key],
            ).fetchone()
            if existing:
                row = self._conn.execute(
                    f"SELECT {_CONV_COLS} FROM app_crm_customer_conversion WHERE id = ?",
                    [int(existing[0])],
                ).fetchone()
                return _map_conversion(row), None

        now = _now()
        cid = _next_id(self._conn, "app_crm_customer_conversion")
        raw_token: Optional[str] = None
        claim_token_hash: Optional[str] = None
        claim_token_expires_at = None
        initial_status = "pending"

        if mode == "create_org":
            raw_token = secrets.token_urlsafe(32)
            claim_token_hash = _hash_token(raw_token)
            claim_token_expires_at = now + timedelta(hours=_CLAIM_TOKEN_TTL_HOURS)
            initial_status = "awaiting_customer_claim"

        self._conn.execute(
            f"""
            INSERT INTO app_crm_customer_conversion
                ({_CONV_COLS})
            VALUES (?, ?, ?, ?, NULL, ?, NULL, ?, ?, NULL, ?, ?, NULL, NULL, ?, ?)
            """,
            [cid, opportunity_id, mode, initial_status,
             contact_id, claim_token_hash, claim_token_expires_at,
             idempotency_key, actor_user_id, now, now],
        )
        conv = self._get_or_raise(cid)
        _audit(
            self._conn,
            action="crm.conversion.prepared",
            target_type="crm_customer_conversion",
            target_id=str(cid),
            actor_user_id=actor_user_id,
            new_values={"mode": mode, "status": initial_status, "opportunity_id": opportunity_id},
            request_id=request_id,
        )
        return conv, raw_token

    def confirm_link(
        self,
        conversion_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        request_id: Optional[str] = None,
    ) -> CustomerConversion:
        """Path A: an authenticated org OWNER confirms the link.

        Actor must be an owner of organization_id in app_organization_member/app_member_role.
        This is verified by the presentation layer (dependencies).
        """
        conv = self._get_or_raise(conversion_id)
        if conv.mode != "link_existing":
            raise ValidationError("confirm_link is only valid for link_existing conversions")
        if conv.status not in ("pending",):
            raise ValidationError(f"Cannot confirm conversion in status={conv.status}")

        now = _now()
        self._conn.execute(
            """
            UPDATE app_crm_customer_conversion
            SET status = 'completed', organization_id = ?, signatory_user_id = ?,
                completed_at = ?, updated_at = ?
            WHERE id = ?
            """,
            [organization_id, actor_user_id, now, now, conversion_id],
        )
        # Mark prospect as converted
        self._conn.execute(
            """
            UPDATE app_crm_opportunity
            SET organization_id = ?, updated_at = ?
            WHERE id = ?
            """,
            [organization_id, now, conv.opportunity_id],
        )
        updated = self._get_or_raise(conversion_id)
        _audit(
            self._conn,
            action="crm.conversion.completed",
            target_type="crm_customer_conversion",
            target_id=str(conversion_id),
            actor_user_id=actor_user_id,
            previous_values={"status": conv.status},
            new_values={"status": "completed", "organization_id": organization_id},
            request_id=request_id,
        )
        return updated

    def claim(
        self,
        conversion_id: int,
        *,
        raw_token: str,
        actor_user_id: int,
        org_display_name: str,
        org_slug: str,
        org_type: str = "prospect",
        timezone: str = "UTC",
        default_currency: str = "USD",
        country_code: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> CustomerConversion:
        """Path B: the authenticated signatory claims the token and creates an org.

        Raw token is checked once (hashed on arrival).
        Then CreateOrganization from organizations package is called with signatory as actor.
        Token is consumed and single-use enforced.
        The signatory user is NOT set as owner of CRM entities.
        """
        conv = self._get_or_raise(conversion_id)
        if conv.mode != "create_org":
            raise ValidationError("claim is only valid for create_org conversions")
        if conv.status != "awaiting_customer_claim":
            if conv.status == "completed" and conv.claim_consumed_at is not None:
                raise TokenAlreadyUsedError("Token has already been consumed")
            raise ValidationError(f"Conversion not in awaiting_customer_claim state (status={conv.status})")
        if conv.claim_consumed_at is not None:
            raise TokenAlreadyUsedError("Token has already been consumed")

        # Check token validity
        token_hash = _hash_token(raw_token)
        if conv.claim_token_hash != token_hash:
            raise TokenExpiredError("Invalid or expired claim token")

        now = _now()
        if conv.claim_token_expires_at and conv.claim_token_expires_at < now:
            raise TokenExpiredError("Claim token has expired")

        # Mark token as consumed immediately to prevent double-use
        self._conn.execute(
            "UPDATE app_crm_customer_conversion SET claim_consumed_at = ?, status = 'processing', updated_at = ? WHERE id = ?",
            [now, now, conversion_id],
        )

        # Call CreateOrganization with signatory as actor
        from app.packages.organizations.application.dto import (
            ActorContext,
            CreateOrganizationCommand,
        )
        from app.packages.organizations.application.use_cases.create_organization import (
            CreateOrganization,
        )

        actor = ActorContext(
            user_id=actor_user_id,
            platform_role=None,
            request_id=request_id,
        )
        cmd = CreateOrganizationCommand(
            actor=actor,
            display_name=org_display_name,
            slug=org_slug,
            organization_type=org_type,
            country_code=country_code,
            timezone=timezone,
            default_currency=default_currency,
            legal_name=None,
            make_active=True,
        )
        try:
            org_result = CreateOrganization(self._conn).execute(cmd)
            organization_id = org_result.organization.id
        except Exception as exc:
            # Rollback to failed
            self._conn.execute(
                "UPDATE app_crm_customer_conversion SET status = 'failed', failure_reason = ?, updated_at = ? WHERE id = ?",
                [str(exc)[:500], now, conversion_id],
            )
            raise PersistenceError(f"Failed to create organization: {exc}") from exc

        self._conn.execute(
            """
            UPDATE app_crm_customer_conversion
            SET status = 'completed', organization_id = ?, signatory_user_id = ?,
                completed_at = ?, updated_at = ?
            WHERE id = ?
            """,
            [organization_id, actor_user_id, now, now, conversion_id],
        )
        self._conn.execute(
            "UPDATE app_crm_opportunity SET organization_id = ?, updated_at = ? WHERE id = ?",
            [organization_id, now, conv.opportunity_id],
        )
        updated = self._get_or_raise(conversion_id)
        _audit(
            self._conn,
            action="crm.conversion.claimed",
            target_type="crm_customer_conversion",
            target_id=str(conversion_id),
            actor_user_id=actor_user_id,
            new_values={
                "status": "completed",
                "organization_id": organization_id,
                "mode": "create_org",
            },
            request_id=request_id,
        )
        return updated

    def get(self, conversion_id: int) -> CustomerConversion:
        return self._get_or_raise(conversion_id)

    def list(
        self,
        *,
        opportunity_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[CustomerConversion], int]:
        conditions: list[str] = []
        params: list[Any] = []
        if opportunity_id is not None:
            conditions.append("opportunity_id = ?")
            params.append(opportunity_id)
        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        where = " AND ".join(conditions) if conditions else "1=1"
        total = int(
            self._conn.execute(
                f"SELECT COUNT(*) FROM app_crm_customer_conversion WHERE {where}", params
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_CONV_COLS} FROM app_crm_customer_conversion WHERE {where} "
            f"ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [_map_conversion(r) for r in rows], total

    def _get_or_raise(self, conversion_id: int) -> CustomerConversion:
        row = self._conn.execute(
            f"SELECT {_CONV_COLS} FROM app_crm_customer_conversion WHERE id = ?",
            [conversion_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"conversion id={conversion_id}")
        return _map_conversion(row)
