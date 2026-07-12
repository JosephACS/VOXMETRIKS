"""Commercial contract repository — Spec 017."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now

_SELECT = (
    "id, quotation_version_id, opportunity_id, organization_id, legal_name, "
    "signatory_user_id, signatory_contact_id, terms_snapshot, status, "
    "acceptance_evidence, accepted_at, rejected_at, expired_at, terminated_at, "
    "termination_reason, approved_by, approved_at, approval_notes, "
    "created_by, created_at, updated_at"
)


@dataclass(frozen=True)
class CommercialContract:
    id: int
    quotation_version_id: int
    opportunity_id: int
    organization_id: Optional[int]
    legal_name: str
    signatory_user_id: Optional[int]
    signatory_contact_id: Optional[int]
    terms_snapshot: Optional[str]
    status: str
    acceptance_evidence: Optional[str]
    accepted_at: Optional[datetime]
    rejected_at: Optional[datetime]
    expired_at: Optional[datetime]
    terminated_at: Optional[datetime]
    termination_reason: Optional[str]
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    approval_notes: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime


def _map(row: tuple) -> CommercialContract:
    return CommercialContract(
        id=int(row[0]),
        quotation_version_id=int(row[1]),
        opportunity_id=int(row[2]),
        organization_id=int(row[3]) if row[3] is not None else None,
        legal_name=str(row[4]),
        signatory_user_id=int(row[5]) if row[5] is not None else None,
        signatory_contact_id=int(row[6]) if row[6] is not None else None,
        terms_snapshot=row[7],
        status=str(row[8]),
        acceptance_evidence=row[9],
        accepted_at=row[10],
        rejected_at=row[11],
        expired_at=row[12],
        terminated_at=row[13],
        termination_reason=row[14],
        approved_by=int(row[15]) if row[15] is not None else None,
        approved_at=row[16],
        approval_notes=row[17],
        created_by=int(row[18]),
        created_at=row[19],
        updated_at=row[20],
    )


def _next_id(conn: duckdb.DuckDBPyConnection) -> int:
    row = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_commercial_contract").fetchone()
    return int(row[0])


class CommercialContractRepository:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        quotation_version_id: int,
        opportunity_id: int,
        legal_name: str,
        created_by: int,
        organization_id: Optional[int] = None,
        signatory_user_id: Optional[int] = None,
        signatory_contact_id: Optional[int] = None,
        terms_snapshot: Optional[str] = None,
    ) -> CommercialContract:
        now = utc_now()
        cid = _next_id(self._conn)
        self._conn.execute(
            f"""
            INSERT INTO app_commercial_contract
                ({_SELECT})
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, ?, ?, ?)
            """,
            [cid, quotation_version_id, opportunity_id, organization_id, legal_name,
             signatory_user_id, signatory_contact_id, terms_snapshot,
             created_by, now, now],
        )
        return self.get_or_raise(cid)

    def get_or_raise(self, contract_id: int) -> CommercialContract:
        row = self._conn.execute(
            f"SELECT {_SELECT} FROM app_commercial_contract WHERE id = ?",
            [contract_id],
        ).fetchone()
        if not row:
            raise KeyError(f"contract id={contract_id} not found")
        return _map(row)

    def list(
        self,
        *,
        opportunity_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[CommercialContract], int]:
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
                f"SELECT COUNT(*) FROM app_commercial_contract WHERE {where}", params
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_SELECT} FROM app_commercial_contract WHERE {where} "
            f"ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [_map(r) for r in rows], total

    def update_status(
        self,
        contract_id: int,
        *,
        status: str,
        extra_fields: Optional[dict[str, Any]] = None,
    ) -> CommercialContract:
        now = utc_now()
        fields = ["status = ?", "updated_at = ?"]
        params: list[Any] = [status, now]
        if extra_fields:
            for col, val in extra_fields.items():
                fields.append(f"{col} = ?")
                params.append(val)
        params.append(contract_id)
        self._conn.execute(
            f"UPDATE app_commercial_contract SET {', '.join(fields)} WHERE id = ?", params
        )
        return self.get_or_raise(contract_id)
