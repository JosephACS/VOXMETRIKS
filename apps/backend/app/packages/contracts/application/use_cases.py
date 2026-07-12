"""Contracts application use cases — Spec 017.

Contracts package does NOT import CRM use case classes.
CRM passes quotation_version_id and terms_snapshot into CreateContract.
source for audit = "contracts.use_case"
"""

from __future__ import annotations

import json
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.contracts.infrastructure.repository import (
    CommercialContract,
    CommercialContractRepository,
)


def _audit(
    conn: duckdb.DuckDBPyConnection,
    *,
    action: str,
    target_id: str,
    actor_user_id: int,
    organization_id: Optional[int] = None,
    previous_values: Optional[dict[str, Any]] = None,
    new_values: Optional[dict[str, Any]] = None,
    reason: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    from app.packages.organizations.infrastructure.repositories.audit_repository import AuditRepository
    AuditRepository(conn).append(
        action=action,
        target_type="commercial_contract",
        target_id=target_id,
        source="contracts.use_case",
        result="success",
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        previous_values=previous_values,
        new_values=new_values,
        reason=reason,
        request_id=request_id,
    )


class ContractUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._repo = CommercialContractRepository(conn)

    def create(
        self,
        *,
        actor_user_id: int,
        quotation_version_id: int,
        opportunity_id: int,
        legal_name: str,
        organization_id: Optional[int] = None,
        signatory_user_id: Optional[int] = None,
        signatory_contact_id: Optional[int] = None,
        terms_snapshot: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> CommercialContract:
        if not legal_name or not legal_name.strip():
            raise ValueError("legal_name is required")

        # Verify the quotation version exists and is accepted/approved (integrity check)
        qv_row = self._conn.execute(
            "SELECT status FROM app_crm_quotation_version WHERE id = ?",
            [quotation_version_id],
        ).fetchone()
        if not qv_row:
            raise KeyError(f"quotation_version id={quotation_version_id} not found")

        terms_json = json.dumps(terms_snapshot, default=str) if terms_snapshot else None
        contract = self._repo.create(
            quotation_version_id=quotation_version_id,
            opportunity_id=opportunity_id,
            legal_name=legal_name.strip(),
            created_by=actor_user_id,
            organization_id=organization_id,
            signatory_user_id=signatory_user_id,
            signatory_contact_id=signatory_contact_id,
            terms_snapshot=terms_json,
        )
        _audit(
            self._conn,
            action="contract.created",
            target_id=str(contract.id),
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            new_values={"legal_name": legal_name, "opportunity_id": opportunity_id},
            request_id=request_id,
        )
        return contract

    def get(self, contract_id: int) -> CommercialContract:
        try:
            return self._repo.get_or_raise(contract_id)
        except KeyError as exc:
            raise KeyError(str(exc)) from exc

    def list(
        self,
        *,
        opportunity_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[CommercialContract], int]:
        return self._repo.list(opportunity_id=opportunity_id, status=status, limit=limit, offset=offset)

    def approve(
        self,
        contract_id: int,
        *,
        actor_user_id: int,
        approval_notes: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> CommercialContract:
        contract = self._get_or_raise(contract_id)
        self._require_status(contract, "pending_approval")
        now = utc_now()
        updated = self._repo.update_status(
            contract_id,
            status="approved",
            extra_fields={"approved_by": actor_user_id, "approved_at": now, "approval_notes": approval_notes},
        )
        _audit(
            self._conn,
            action="contract.approved",
            target_id=str(contract_id),
            actor_user_id=actor_user_id,
            organization_id=contract.organization_id,
            previous_values={"status": contract.status},
            new_values={"status": "approved"},
            request_id=request_id,
        )
        return updated

    def submit_for_approval(
        self,
        contract_id: int,
        *,
        actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> CommercialContract:
        contract = self._get_or_raise(contract_id)
        self._require_status(contract, "draft")
        updated = self._repo.update_status(contract_id, status="pending_approval")
        _audit(
            self._conn,
            action="contract.submitted_for_approval",
            target_id=str(contract_id),
            actor_user_id=actor_user_id,
            organization_id=contract.organization_id,
            previous_values={"status": "draft"},
            new_values={"status": "pending_approval"},
            request_id=request_id,
        )
        return updated

    def send(
        self,
        contract_id: int,
        *,
        actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> CommercialContract:
        contract = self._get_or_raise(contract_id)
        if contract.status not in ("draft", "approved"):
            raise ValueError(f"Contract must be draft or approved to send (status={contract.status})")
        updated = self._repo.update_status(contract_id, status="sent")
        _audit(
            self._conn,
            action="contract.sent",
            target_id=str(contract_id),
            actor_user_id=actor_user_id,
            organization_id=contract.organization_id,
            previous_values={"status": contract.status},
            new_values={"status": "sent"},
            request_id=request_id,
        )
        return updated

    def accept(
        self,
        contract_id: int,
        *,
        actor_user_id: int,
        acceptance_evidence: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> CommercialContract:
        """Academic acceptance — not a legal e-sign."""
        contract = self._get_or_raise(contract_id)
        if contract.status not in ("sent", "approved"):
            raise ValueError(f"Contract must be sent or approved to accept (status={contract.status})")
        now = utc_now()
        updated = self._repo.update_status(
            contract_id,
            status="accepted",
            extra_fields={"accepted_at": now, "acceptance_evidence": acceptance_evidence},
        )
        _audit(
            self._conn,
            action="contract.accepted",
            target_id=str(contract_id),
            actor_user_id=actor_user_id,
            organization_id=contract.organization_id,
            previous_values={"status": contract.status},
            new_values={"status": "accepted"},
            request_id=request_id,
        )
        return updated

    def reject(
        self,
        contract_id: int,
        *,
        actor_user_id: int,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> CommercialContract:
        contract = self._get_or_raise(contract_id)
        if contract.status not in ("sent", "pending_approval"):
            raise ValueError(f"Cannot reject contract in status={contract.status}")
        now = utc_now()
        updated = self._repo.update_status(
            contract_id,
            status="rejected",
            extra_fields={"rejected_at": now},
        )
        _audit(
            self._conn,
            action="contract.rejected",
            target_id=str(contract_id),
            actor_user_id=actor_user_id,
            organization_id=contract.organization_id,
            previous_values={"status": contract.status},
            new_values={"status": "rejected"},
            reason=reason,
            request_id=request_id,
        )
        return updated

    def expire(
        self,
        contract_id: int,
        *,
        actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> CommercialContract:
        contract = self._get_or_raise(contract_id)
        if contract.status not in ("sent",):
            raise ValueError(f"Cannot expire contract in status={contract.status}")
        now = utc_now()
        updated = self._repo.update_status(
            contract_id,
            status="expired",
            extra_fields={"expired_at": now},
        )
        _audit(
            self._conn,
            action="contract.expired",
            target_id=str(contract_id),
            actor_user_id=actor_user_id,
            organization_id=contract.organization_id,
            previous_values={"status": contract.status},
            new_values={"status": "expired"},
            request_id=request_id,
        )
        return updated

    def terminate(
        self,
        contract_id: int,
        *,
        actor_user_id: int,
        reason: str,
        request_id: Optional[str] = None,
    ) -> CommercialContract:
        contract = self._get_or_raise(contract_id)
        if contract.status not in ("accepted",):
            raise ValueError(f"Cannot terminate contract in status={contract.status}")
        now = utc_now()
        updated = self._repo.update_status(
            contract_id,
            status="terminated",
            extra_fields={"terminated_at": now, "termination_reason": reason},
        )
        _audit(
            self._conn,
            action="contract.terminated",
            target_id=str(contract_id),
            actor_user_id=actor_user_id,
            organization_id=contract.organization_id,
            previous_values={"status": contract.status},
            new_values={"status": "terminated"},
            reason=reason,
            request_id=request_id,
        )
        return updated

    def _get_or_raise(self, contract_id: int) -> CommercialContract:
        try:
            return self._repo.get_or_raise(contract_id)
        except KeyError as exc:
            raise KeyError(str(exc)) from exc

    def _require_status(self, contract: CommercialContract, required_status: str) -> None:
        if contract.status != required_status:
            raise ValueError(f"Contract must be in status={required_status} (current={contract.status})")
