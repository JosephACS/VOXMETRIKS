"""Compliance use cases — Spec 026."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.compliance.domain.entities import (
    AuditLogEntry,
    ConsentDefinition,
    ConsentRecord,
    DataRequest,
    DataRequestAction,
    IncidentAction,
    LegalHold,
    RetentionExecution,
    RetentionPolicy,
    SecurityIncident,
    SensitiveAccessRecord,
    TermsAcceptance,
    TermsVersion,
)
from app.packages.compliance.domain.errors import (
    DeletionBlockedError,
    NotFoundError,
    StateError,
    ValidationError,
)


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    return int(conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()[0])


def _now() -> datetime:
    return utc_now()


def _audit(
    conn: duckdb.DuckDBPyConnection,
    *,
    action: str,
    target_type: str,
    target_id: str,
    actor_user_id: Optional[int],
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
            source="compliance.use_case",
            result="success",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            previous_values=previous_values,
            new_values=new_values,
            reason=reason,
            request_id=request_id,
        )
    except Exception:
        pass


def _sanitize_export(data: dict[str, Any]) -> dict[str, Any]:
    """Minimize PII in export payloads."""
    forbidden = {"password", "token", "secret", "pan", "cvv", "ssn"}
    out: dict[str, Any] = {}
    for k, v in data.items():
        if k.lower() in forbidden:
            continue
        if isinstance(v, dict):
            out[k] = _sanitize_export(v)
        else:
            out[k] = v
    return out


class TermsVersionUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def list(self, *, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> tuple[list[TermsVersion], int]:
        where = "WHERE status = ?" if status else ""
        params: list[Any] = [status] if status else []
        total = int(self._conn.execute(f"SELECT COUNT(*) FROM app_terms_version {where}", params).fetchone()[0])
        rows = self._conn.execute(
            f"""
            SELECT id, version_code, title, content_summary, effective_at, status,
                   created_by, created_at, updated_at
            FROM app_terms_version {where}
            ORDER BY effective_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        ).fetchall()
        items = [TermsVersion(*r) for r in rows]
        return items, total

    def create(
        self,
        *,
        actor_user_id: int,
        version_code: str,
        title: str,
        content_summary: str,
        effective_at: datetime,
        request_id: Optional[str] = None,
    ) -> TermsVersion:
        if not version_code.strip() or not title.strip():
            raise ValidationError("version_code and title are required")
        now = _now()
        vid = _next_id(self._conn, "app_terms_version")
        self._conn.execute(
            """
            INSERT INTO app_terms_version
                (id, version_code, title, content_summary, effective_at, status,
                 created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'draft', ?, ?, ?)
            """,
            [vid, version_code.strip(), title.strip(), content_summary, effective_at,
             actor_user_id, now, now],
        )
        _audit(self._conn, action="terms_version.created", target_type="terms_version",
               target_id=str(vid), actor_user_id=actor_user_id, new_values={"version_code": version_code},
               request_id=request_id)
        return self.get(vid)

    def get(self, version_id: int) -> TermsVersion:
        row = self._conn.execute(
            """
            SELECT id, version_code, title, content_summary, effective_at, status,
                   created_by, created_at, updated_at
            FROM app_terms_version WHERE id = ?
            """,
            [version_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"Terms version {version_id} not found")
        return TermsVersion(*row)

    def publish(self, version_id: int, *, actor_user_id: int, request_id: Optional[str] = None) -> TermsVersion:
        tv = self.get(version_id)
        if tv.status != "draft":
            raise StateError(f"Cannot publish terms in status {tv.status}")
        now = _now()
        self._conn.execute(
            "UPDATE app_terms_version SET status = 'published', updated_at = ? WHERE id = ?",
            [now, version_id],
        )
        _audit(self._conn, action="terms_version.published", target_type="terms_version",
               target_id=str(version_id), actor_user_id=actor_user_id, request_id=request_id)
        return self.get(version_id)


class TermsAcceptanceUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def accept(
        self,
        *,
        user_id: int,
        terms_version_id: int,
        organization_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> TermsAcceptance:
        tv_row = self._conn.execute(
            "SELECT status FROM app_terms_version WHERE id = ?", [terms_version_id],
        ).fetchone()
        if not tv_row or tv_row[0] != "published":
            raise ValidationError("Can only accept published terms versions")
        now = _now()
        aid = _next_id(self._conn, "app_terms_acceptance")
        self._conn.execute(
            """
            INSERT INTO app_terms_acceptance
                (id, terms_version_id, user_id, organization_id, accepted_at, ip_address, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [aid, terms_version_id, user_id, organization_id, now, ip_address, now],
        )
        _audit(self._conn, action="terms.accepted", target_type="terms_acceptance",
               target_id=str(aid), actor_user_id=user_id, organization_id=organization_id,
               new_values={"terms_version_id": terms_version_id}, request_id=request_id)
        row = self._conn.execute(
            """
            SELECT id, terms_version_id, user_id, organization_id, accepted_at, ip_address, created_at
            FROM app_terms_acceptance WHERE id = ?
            """,
            [aid],
        ).fetchone()
        return TermsAcceptance(*row)

    def list_for_user(self, user_id: int, *, organization_id: Optional[int] = None) -> list[TermsAcceptance]:
        if organization_id:
            rows = self._conn.execute(
                """
                SELECT id, terms_version_id, user_id, organization_id, accepted_at, ip_address, created_at
                FROM app_terms_acceptance
                WHERE user_id = ? AND (organization_id = ? OR organization_id IS NULL)
                ORDER BY accepted_at DESC
                """,
                [user_id, organization_id],
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT id, terms_version_id, user_id, organization_id, accepted_at, ip_address, created_at
                FROM app_terms_acceptance WHERE user_id = ? ORDER BY accepted_at DESC
                """,
                [user_id],
            ).fetchall()
        return [TermsAcceptance(*r) for r in rows]


class ConsentDefinitionUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def list(
        self,
        *,
        organization_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ConsentDefinition], int]:
        if organization_id:
            total = int(self._conn.execute(
                "SELECT COUNT(*) FROM app_consent_definition WHERE organization_id = ? OR organization_id IS NULL",
                [organization_id],
            ).fetchone()[0])
            rows = self._conn.execute(
                """
                SELECT id, organization_id, code, title, description, is_required, status,
                       created_at, updated_at
                FROM app_consent_definition
                WHERE organization_id = ? OR organization_id IS NULL
                ORDER BY code LIMIT ? OFFSET ?
                """,
                [organization_id, limit, offset],
            ).fetchall()
        else:
            total = int(self._conn.execute("SELECT COUNT(*) FROM app_consent_definition").fetchone()[0])
            rows = self._conn.execute(
                """
                SELECT id, organization_id, code, title, description, is_required, status,
                       created_at, updated_at
                FROM app_consent_definition ORDER BY code LIMIT ? OFFSET ?
                """,
                [limit, offset],
            ).fetchall()
        return [ConsentDefinition(*r) for r in rows], total

    def create(
        self,
        *,
        actor_user_id: int,
        code: str,
        title: str,
        description: str,
        organization_id: Optional[int] = None,
        is_required: bool = False,
        request_id: Optional[str] = None,
    ) -> ConsentDefinition:
        if not code.strip():
            raise ValidationError("Consent code is required")
        now = _now()
        cid = _next_id(self._conn, "app_consent_definition")
        self._conn.execute(
            """
            INSERT INTO app_consent_definition
                (id, organization_id, code, title, description, is_required, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
            """,
            [cid, organization_id, code.strip(), title, description, is_required, now, now],
        )
        _audit(self._conn, action="consent_definition.created", target_type="consent_definition",
               target_id=str(cid), actor_user_id=actor_user_id, organization_id=organization_id,
               new_values={"code": code}, request_id=request_id)
        return self.get(cid)

    def get(self, definition_id: int) -> ConsentDefinition:
        row = self._conn.execute(
            """
            SELECT id, organization_id, code, title, description, is_required, status,
                   created_at, updated_at
            FROM app_consent_definition WHERE id = ?
            """,
            [definition_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"Consent definition {definition_id} not found")
        return ConsentDefinition(*row)


class ConsentRecordUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def grant(
        self,
        *,
        user_id: int,
        consent_definition_id: int,
        organization_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> ConsentRecord:
        ConsentDefinitionUseCases(self._conn).get(consent_definition_id)
        now = _now()
        rid = _next_id(self._conn, "app_consent_record")
        self._conn.execute(
            """
            INSERT INTO app_consent_record
                (id, consent_definition_id, user_id, organization_id, status,
                 granted_at, withdrawn_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'granted', ?, NULL, ?, ?)
            """,
            [rid, consent_definition_id, user_id, organization_id, now, now, now],
        )
        _audit(self._conn, action="consent.granted", target_type="consent_record",
               target_id=str(rid), actor_user_id=user_id, organization_id=organization_id,
               request_id=request_id)
        return self._get(rid)

    def withdraw(
        self,
        record_id: int,
        *,
        user_id: int,
        organization_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> ConsentRecord:
        rec = self._get(record_id)
        if rec.user_id != user_id:
            raise ValidationError("Only the consent subject can withdraw")
        if rec.status == "withdrawn":
            raise StateError("Consent already withdrawn")
        now = _now()
        self._conn.execute(
            """
            UPDATE app_consent_record
            SET status = 'withdrawn', withdrawn_at = ?, updated_at = ?
            WHERE id = ?
            """,
            [now, now, record_id],
        )
        _audit(self._conn, action="consent.withdrawn", target_type="consent_record",
               target_id=str(record_id), actor_user_id=user_id, organization_id=organization_id,
               request_id=request_id)
        return self._get(record_id)

    def list_for_user(self, user_id: int, *, organization_id: Optional[int] = None) -> list[ConsentRecord]:
        if organization_id:
            rows = self._conn.execute(
                """
                SELECT id, consent_definition_id, user_id, organization_id, status,
                       granted_at, withdrawn_at, created_at, updated_at
                FROM app_consent_record
                WHERE user_id = ? AND (organization_id = ? OR organization_id IS NULL)
                ORDER BY updated_at DESC
                """,
                [user_id, organization_id],
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT id, consent_definition_id, user_id, organization_id, status,
                       granted_at, withdrawn_at, created_at, updated_at
                FROM app_consent_record WHERE user_id = ? ORDER BY updated_at DESC
                """,
                [user_id],
            ).fetchall()
        return [ConsentRecord(*r) for r in rows]

    def _get(self, record_id: int) -> ConsentRecord:
        row = self._conn.execute(
            """
            SELECT id, consent_definition_id, user_id, organization_id, status,
                   granted_at, withdrawn_at, created_at, updated_at
            FROM app_consent_record WHERE id = ?
            """,
            [record_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"Consent record {record_id} not found")
        return ConsentRecord(*row)


class LegalHoldUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def has_active_hold(self, organization_id: int, subject_type: str, subject_id: str) -> bool:
        row = self._conn.execute(
            """
            SELECT 1 FROM app_legal_hold
            WHERE organization_id = ? AND subject_type = ? AND subject_id = ?
              AND status = 'active'
            LIMIT 1
            """,
            [organization_id, subject_type, subject_id],
        ).fetchone()
        return row is not None

    def place(
        self,
        *,
        actor_user_id: int,
        organization_id: int,
        subject_type: str,
        subject_id: str,
        reason: str,
        request_id: Optional[str] = None,
    ) -> LegalHold:
        if not reason.strip():
            raise ValidationError("Legal hold reason is required")
        now = _now()
        hid = _next_id(self._conn, "app_legal_hold")
        self._conn.execute(
            """
            INSERT INTO app_legal_hold
                (id, organization_id, subject_type, subject_id, status, reason,
                 placed_by, placed_at, released_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'active', ?, ?, ?, NULL, ?, ?)
            """,
            [hid, organization_id, subject_type, subject_id, reason.strip(),
             actor_user_id, now, now, now],
        )
        _audit(self._conn, action="legal_hold.placed", target_type="legal_hold",
               target_id=str(hid), actor_user_id=actor_user_id, organization_id=organization_id,
               reason=reason, request_id=request_id)
        return self.get(hid, organization_id)

    def release(
        self,
        hold_id: int,
        organization_id: int,
        *,
        actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> LegalHold:
        hold = self.get(hold_id, organization_id)
        if hold.status != "active":
            raise StateError("Legal hold is not active")
        now = _now()
        self._conn.execute(
            "UPDATE app_legal_hold SET status = 'released', released_at = ?, updated_at = ? WHERE id = ?",
            [now, now, hold_id],
        )
        _audit(self._conn, action="legal_hold.released", target_type="legal_hold",
               target_id=str(hold_id), actor_user_id=actor_user_id, organization_id=organization_id,
               request_id=request_id)
        return self.get(hold_id, organization_id)

    def get(self, hold_id: int, organization_id: int) -> LegalHold:
        row = self._conn.execute(
            """
            SELECT id, organization_id, subject_type, subject_id, status, reason,
                   placed_by, placed_at, released_at, created_at, updated_at
            FROM app_legal_hold WHERE id = ? AND organization_id = ?
            """,
            [hold_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"Legal hold {hold_id} not found")
        return LegalHold(*row)

    def list(self, organization_id: int, *, status: Optional[str] = None) -> list[LegalHold]:
        if status:
            rows = self._conn.execute(
                """
                SELECT id, organization_id, subject_type, subject_id, status, reason,
                       placed_by, placed_at, released_at, created_at, updated_at
                FROM app_legal_hold WHERE organization_id = ? AND status = ?
                ORDER BY placed_at DESC
                """,
                [organization_id, status],
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT id, organization_id, subject_type, subject_id, status, reason,
                       placed_by, placed_at, released_at, created_at, updated_at
                FROM app_legal_hold WHERE organization_id = ?
                ORDER BY placed_at DESC
                """,
                [organization_id],
            ).fetchall()
        return [LegalHold(*r) for r in rows]


class RetentionPolicyUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        organization_id: int,
        data_category: str,
        retention_days: int,
        description: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> RetentionPolicy:
        if retention_days <= 0:
            raise ValidationError("retention_days must be positive")
        now = _now()
        pid = _next_id(self._conn, "app_retention_policy")
        self._conn.execute(
            """
            INSERT INTO app_retention_policy
                (id, organization_id, data_category, retention_days, status, description,
                 created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?)
            """,
            [pid, organization_id, data_category, retention_days, description,
             actor_user_id, now, now],
        )
        _audit(self._conn, action="retention_policy.created", target_type="retention_policy",
               target_id=str(pid), actor_user_id=actor_user_id, organization_id=organization_id,
               request_id=request_id)
        return self.get(pid, organization_id)

    def get(self, policy_id: int, organization_id: int) -> RetentionPolicy:
        row = self._conn.execute(
            """
            SELECT id, organization_id, data_category, retention_days, status, description,
                   created_by, created_at, updated_at
            FROM app_retention_policy WHERE id = ? AND organization_id = ?
            """,
            [policy_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"Retention policy {policy_id} not found")
        return RetentionPolicy(*row)

    def list(self, organization_id: int) -> list[RetentionPolicy]:
        rows = self._conn.execute(
            """
            SELECT id, organization_id, data_category, retention_days, status, description,
                   created_by, created_at, updated_at
            FROM app_retention_policy WHERE organization_id = ? ORDER BY data_category
            """,
            [organization_id],
        ).fetchall()
        return [RetentionPolicy(*r) for r in rows]

    def execute(
        self,
        policy_id: int,
        organization_id: int,
        *,
        actor_user_id: int,
        records_evaluated: int = 0,
        records_blocked: int = 0,
        request_id: Optional[str] = None,
    ) -> RetentionExecution:
        self.get(policy_id, organization_id)
        now = _now()
        eid = _next_id(self._conn, "app_retention_execution")
        status = "completed" if records_blocked == 0 else "partial"
        self._conn.execute(
            """
            INSERT INTO app_retention_execution
                (id, retention_policy_id, organization_id, status, records_evaluated,
                 records_blocked, executed_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [eid, policy_id, organization_id, status, records_evaluated,
             records_blocked, now, now],
        )
        _audit(self._conn, action="retention.executed", target_type="retention_execution",
               target_id=str(eid), actor_user_id=actor_user_id, organization_id=organization_id,
               request_id=request_id)
        row = self._conn.execute(
            """
            SELECT id, retention_policy_id, organization_id, status, records_evaluated,
                   records_blocked, executed_at, created_at
            FROM app_retention_execution WHERE id = ?
            """,
            [eid],
        ).fetchone()
        return RetentionExecution(*row)


class DataRequestUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def _get(self, request_id: int, organization_id: int) -> DataRequest:
        row = self._conn.execute(
            """
            SELECT id, organization_id, requester_user_id, request_type, status,
                   subject_user_id, reason, requested_at, completed_at, created_at, updated_at
            FROM app_data_request WHERE id = ? AND organization_id = ?
            """,
            [request_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"Data request {request_id} not found")
        return DataRequest(*row)

    def submit(
        self,
        *,
        requester_user_id: int,
        organization_id: int,
        request_type: str,
        subject_user_id: Optional[int] = None,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> DataRequest:
        valid_types = {"access", "export", "correction", "deletion"}
        if request_type not in valid_types:
            raise ValidationError(f"Invalid request_type: {request_type}")
        now = _now()
        rid = _next_id(self._conn, "app_data_request")
        self._conn.execute(
            """
            INSERT INTO app_data_request
                (id, organization_id, requester_user_id, request_type, status,
                 subject_user_id, reason, requested_at, completed_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'submitted', ?, ?, ?, NULL, ?, ?)
            """,
            [rid, organization_id, requester_user_id, request_type,
             subject_user_id or requester_user_id, reason, now, now, now],
        )
        _audit(self._conn, action="dsr.submitted", target_type="data_request",
               target_id=str(rid), actor_user_id=requester_user_id, organization_id=organization_id,
               new_values={"request_type": request_type}, request_id=request_id)
        return self._get(rid, organization_id)

    def list(
        self,
        organization_id: int,
        *,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[DataRequest], int]:
        where = "WHERE organization_id = ?"
        params: list[Any] = [organization_id]
        if status:
            where += " AND status = ?"
            params.append(status)
        total = int(self._conn.execute(f"SELECT COUNT(*) FROM app_data_request {where}", params).fetchone()[0])
        rows = self._conn.execute(
            f"""
            SELECT id, organization_id, requester_user_id, request_type, status,
                   subject_user_id, reason, requested_at, completed_at, created_at, updated_at
            FROM app_data_request {where}
            ORDER BY requested_at DESC LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        ).fetchall()
        return [DataRequest(*r) for r in rows], total

    def process_deletion(
        self,
        data_request_id: int,
        organization_id: int,
        *,
        actor_user_id: int,
        subject_type: str = "user",
        subject_id: str = "",
        request_id: Optional[str] = None,
    ) -> DataRequestAction:
        dr = self._get(data_request_id, organization_id)
        if dr.request_type != "deletion":
            raise ValidationError("Not a deletion request")
        if dr.status in ("completed", "blocked"):
            raise StateError(f"Request already {dr.status}")

        blockers: list[str] = []
        sid = subject_id or str(dr.subject_user_id or dr.requester_user_id)
        if LegalHoldUseCases(self._conn).has_active_hold(organization_id, subject_type, sid):
            blockers.append("legal_hold")

        active_policies = self._conn.execute(
            "SELECT COUNT(*) FROM app_retention_policy WHERE organization_id = ? AND status = 'active'",
            [organization_id],
        ).fetchone()[0]
        if int(active_policies) > 0:
            blockers.append("retention_policy")

        now = _now()
        aid = _next_id(self._conn, "app_data_request_action")

        if blockers:
            self._conn.execute(
                "UPDATE app_data_request SET status = 'blocked', updated_at = ? WHERE id = ?",
                [now, data_request_id],
            )
            self._conn.execute(
                """
                INSERT INTO app_data_request_action
                    (id, data_request_id, organization_id, action_type, status,
                     actor_user_id, notes, export_uri, performed_at, created_at)
                VALUES (?, ?, ?, 'block', 'completed', ?, ?, NULL, ?, ?)
                """,
                [aid, data_request_id, organization_id, actor_user_id,
                 f"Blocked by: {', '.join(blockers)}", now, now],
            )
            _audit(self._conn, action="dsr.deletion_blocked", target_type="data_request",
                   target_id=str(data_request_id), actor_user_id=actor_user_id,
                   organization_id=organization_id, reason=",".join(blockers), request_id=request_id)
            raise DeletionBlockedError(
                "Deletion blocked by legal hold and/or retention policy",
                blockers=blockers,
            )

        self._conn.execute(
            "UPDATE app_data_request SET status = 'completed', completed_at = ?, updated_at = ? WHERE id = ?",
            [now, now, data_request_id],
        )
        self._conn.execute(
            """
            INSERT INTO app_data_request_action
                (id, data_request_id, organization_id, action_type, status,
                 actor_user_id, notes, export_uri, performed_at, created_at)
            VALUES (?, ?, ?, 'delete', 'completed', ?, 'Deletion recorded (no silent delete)', NULL, ?, ?)
            """,
            [aid, data_request_id, organization_id, actor_user_id, now, now],
        )
        _audit(self._conn, action="dsr.deletion_completed", target_type="data_request",
               target_id=str(data_request_id), actor_user_id=actor_user_id,
               organization_id=organization_id, request_id=request_id)
        row = self._conn.execute(
            """
            SELECT id, data_request_id, organization_id, action_type, status,
                   actor_user_id, notes, export_uri, performed_at, created_at
            FROM app_data_request_action WHERE id = ?
            """,
            [aid],
        ).fetchone()
        return DataRequestAction(*row)

    def export_data(
        self,
        data_request_id: int,
        organization_id: int,
        *,
        actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> DataRequestAction:
        dr = self._get(data_request_id, organization_id)
        if dr.request_type not in ("access", "export"):
            raise ValidationError("Not an access/export request")
        now = _now()
        export_payload = _sanitize_export({
            "user_id": dr.subject_user_id or dr.requester_user_id,
            "organization_id": organization_id,
            "request_type": dr.request_type,
            "note": "Sanitized academic export — not a production data dump",
        })
        export_uri = f"export://sanitized/{data_request_id}"
        aid = _next_id(self._conn, "app_data_request_action")
        self._conn.execute(
            """
            INSERT INTO app_data_request_action
                (id, data_request_id, organization_id, action_type, status,
                 actor_user_id, notes, export_uri, performed_at, created_at)
            VALUES (?, ?, ?, 'export', 'completed', ?, ?, ?, ?, ?)
            """,
            [aid, data_request_id, organization_id, actor_user_id,
             json.dumps(export_payload), export_uri, now, now],
        )
        self._conn.execute(
            "UPDATE app_data_request SET status = 'completed', completed_at = ?, updated_at = ? WHERE id = ?",
            [now, now, data_request_id],
        )
        _audit(self._conn, action="dsr.export_completed", target_type="data_request",
               target_id=str(data_request_id), actor_user_id=actor_user_id,
               organization_id=organization_id, request_id=request_id)
        row = self._conn.execute(
            """
            SELECT id, data_request_id, organization_id, action_type, status,
                   actor_user_id, notes, export_uri, performed_at, created_at
            FROM app_data_request_action WHERE id = ?
            """,
            [aid],
        ).fetchone()
        return DataRequestAction(*row)


class SecurityIncidentUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        title: str,
        severity: str,
        description: str,
        organization_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> SecurityIncident:
        if severity not in ("low", "medium", "high", "critical"):
            raise ValidationError("Invalid severity")
        now = _now()
        iid = _next_id(self._conn, "app_security_incident")
        self._conn.execute(
            """
            INSERT INTO app_security_incident
                (id, organization_id, title, severity, status, description,
                 reported_by, reported_at, resolved_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'open', ?, ?, ?, NULL, ?, ?)
            """,
            [iid, organization_id, title, severity, description,
             actor_user_id, now, now, now],
        )
        _audit(self._conn, action="incident.created", target_type="security_incident",
               target_id=str(iid), actor_user_id=actor_user_id, organization_id=organization_id,
               request_id=request_id)
        return self.get(iid, organization_id)

    def get(self, incident_id: int, organization_id: Optional[int] = None) -> SecurityIncident:
        if organization_id:
            row = self._conn.execute(
                """
                SELECT id, organization_id, title, severity, status, description,
                       reported_by, reported_at, resolved_at, created_at, updated_at
                FROM app_security_incident WHERE id = ? AND organization_id = ?
                """,
                [incident_id, organization_id],
            ).fetchone()
        else:
            row = self._conn.execute(
                """
                SELECT id, organization_id, title, severity, status, description,
                       reported_by, reported_at, resolved_at, created_at, updated_at
                FROM app_security_incident WHERE id = ?
                """,
                [incident_id],
            ).fetchone()
        if not row:
            raise NotFoundError(f"Security incident {incident_id} not found")
        return SecurityIncident(*row)

    def add_action(
        self,
        incident_id: int,
        *,
        actor_user_id: int,
        action_type: str,
        description: str,
        organization_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> IncidentAction:
        self.get(incident_id, organization_id)
        now = _now()
        aid = _next_id(self._conn, "app_incident_action")
        self._conn.execute(
            """
            INSERT INTO app_incident_action
                (id, incident_id, organization_id, action_type, description,
                 actor_user_id, performed_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [aid, incident_id, organization_id, action_type, description,
             actor_user_id, now, now],
        )
        _audit(self._conn, action="incident.action_recorded", target_type="incident_action",
               target_id=str(aid), actor_user_id=actor_user_id, organization_id=organization_id,
               request_id=request_id)
        row = self._conn.execute(
            """
            SELECT id, incident_id, organization_id, action_type, description,
                   actor_user_id, performed_at, created_at
            FROM app_incident_action WHERE id = ?
            """,
            [aid],
        ).fetchone()
        return IncidentAction(*row)

    def list(
        self,
        *,
        organization_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SecurityIncident], int]:
        clauses: list[str] = []
        params: list[Any] = []
        if organization_id:
            clauses.append("organization_id = ?")
            params.append(organization_id)
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        total = int(self._conn.execute(
            f"SELECT COUNT(*) FROM app_security_incident {where}", params,
        ).fetchone()[0])
        rows = self._conn.execute(
            f"""
            SELECT id, organization_id, title, severity, status, description,
                   reported_by, reported_at, resolved_at, created_at, updated_at
            FROM app_security_incident {where}
            ORDER BY reported_at DESC LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        ).fetchall()
        return [SecurityIncident(*r) for r in rows], total


class SensitiveAccessUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def record(
        self,
        *,
        accessor_user_id: int,
        resource_type: str,
        resource_id: str,
        reason: str,
        organization_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> SensitiveAccessRecord:
        if not reason.strip():
            raise ValidationError("Sensitive access requires a reason")
        now = _now()
        sid = _next_id(self._conn, "app_sensitive_access_record")
        self._conn.execute(
            """
            INSERT INTO app_sensitive_access_record
                (id, organization_id, accessor_user_id, resource_type, resource_id,
                 reason, accessed_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [sid, organization_id, accessor_user_id, resource_type, resource_id,
             reason.strip(), now, now],
        )
        _audit(self._conn, action="sensitive_access.recorded", target_type="sensitive_access",
               target_id=str(sid), actor_user_id=accessor_user_id, organization_id=organization_id,
               reason=reason, request_id=request_id)
        row = self._conn.execute(
            """
            SELECT id, organization_id, accessor_user_id, resource_type, resource_id,
                   reason, accessed_at, created_at
            FROM app_sensitive_access_record WHERE id = ?
            """,
            [sid],
        ).fetchone()
        return SensitiveAccessRecord(*row)


class AuditSearchUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def search(
        self,
        *,
        organization_id: Optional[int] = None,
        action: Optional[str] = None,
        source: Optional[str] = None,
        actor_user_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
        platform_scope: bool = False,
    ) -> tuple[list[AuditLogEntry], int]:
        clauses: list[str] = []
        params: list[Any] = []

        if platform_scope:
            pass  # no org filter — platform-wide
        elif organization_id is not None:
            clauses.append("organization_id = ?")
            params.append(organization_id)

        if action:
            clauses.append("action LIKE ?")
            params.append(f"%{action}%")
        if source:
            clauses.append("source LIKE ?")
            params.append(f"%{source}%")
        if actor_user_id:
            clauses.append("actor_user_id = ?")
            params.append(actor_user_id)
        if from_date:
            clauses.append("occurred_at >= ?")
            params.append(from_date)
        if to_date:
            clauses.append("occurred_at <= ?")
            params.append(to_date)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        total = int(self._conn.execute(
            f"SELECT COUNT(*) FROM app_audit_log {where}", params,
        ).fetchone()[0])
        rows = self._conn.execute(
            f"""
            SELECT id, organization_id, actor_user_id, action, target_type, target_id,
                   source, result, occurred_at
            FROM app_audit_log {where}
            ORDER BY occurred_at DESC LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        ).fetchall()
        return [AuditLogEntry(*r) for r in rows], total
