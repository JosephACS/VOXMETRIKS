"""Append-only audit log persistence."""

from __future__ import annotations

import json
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.organizations.domain.entities import AuditLogEntry
from app.packages.organizations.domain.errors import OrganizationsError, ValidationError
from app.packages.organizations.infrastructure.repositories._helpers import (
    next_id,
    raise_persistence,
)

_FORBIDDEN_KEYS = frozenset(
    {
        "password",
        "password_hash",
        "token",
        "bearer",
        "authorization",
        "invitation_token",
        "raw_token",
        "pan",
        "cvv",
        "card_number",
        "secret",
        # CRM / Spec 017 — claim token must never appear in audit logs
        "claim_token",
        "token_hash",
        "claim_token_hash",
    }
)

_SELECT = """
    id, organization_id, actor_user_id, actor_platform_role, action,
    target_type, target_id, previous_values_json, new_values_json,
    reason, request_id, source, result, occurred_at
"""


def _map(row: tuple[Any, ...]) -> AuditLogEntry:
    return AuditLogEntry(
        id=int(row[0]),
        organization_id=int(row[1]) if row[1] is not None else None,
        actor_user_id=int(row[2]) if row[2] is not None else None,
        actor_platform_role=row[3],
        action=str(row[4]),
        target_type=str(row[5]),
        target_id=str(row[6]) if row[6] is not None else None,
        previous_values_json=row[7],
        new_values_json=row[8],
        reason=row[9],
        request_id=row[10],
        source=str(row[11]),
        result=str(row[12]),
        occurred_at=row[13],
    )


def _safe_json(values: Optional[dict[str, Any]]) -> Optional[str]:
    if values is None:
        return None
    cleaned: dict[str, Any] = {}
    for key, value in values.items():
        if key.lower() in _FORBIDDEN_KEYS:
            continue
        cleaned[key] = value
    return json.dumps(cleaned, default=str, ensure_ascii=False)


class AuditRepository:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def append(
        self,
        *,
        action: str,
        target_type: str,
        source: str,
        result: str,
        organization_id: Optional[int] = None,
        actor_user_id: Optional[int] = None,
        actor_platform_role: Optional[str] = None,
        target_id: Optional[str] = None,
        previous_values: Optional[dict[str, Any]] = None,
        new_values: Optional[dict[str, Any]] = None,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLogEntry:
        if not action.strip():
            raise ValidationError("action is required")
        if not target_type.strip():
            raise ValidationError("target_type is required")
        if not source.strip():
            raise ValidationError("source is required")
        if not result.strip():
            raise ValidationError("result is required")

        audit_id = next_id(self._conn, "app_audit_log")
        occurred = utc_now()
        try:
            self._conn.execute(
                """
                INSERT INTO app_audit_log (
                    id, organization_id, actor_user_id, actor_platform_role,
                    action, target_type, target_id, previous_values_json,
                    new_values_json, reason, request_id, source, result, occurred_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    audit_id,
                    organization_id,
                    actor_user_id,
                    actor_platform_role,
                    action.strip(),
                    target_type.strip(),
                    target_id,
                    _safe_json(previous_values),
                    _safe_json(new_values),
                    reason,
                    request_id,
                    source.strip(),
                    result.strip(),
                    occurred,
                ],
            )
        except Exception as exc:
            raise_persistence(exc, action="append audit log")
        row = self._conn.execute(
            f"SELECT {_SELECT} FROM app_audit_log WHERE id = ?",
            [audit_id],
        ).fetchone()
        return _map(row)

    def list_by_organization(
        self,
        organization_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLogEntry]:
        if limit < 1:
            raise ValidationError("limit must be >= 1")
        if offset < 0:
            raise ValidationError("offset must be >= 0")
        rows = self._conn.execute(
            f"""
            SELECT {_SELECT} FROM app_audit_log
            WHERE organization_id = ?
            ORDER BY occurred_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            [organization_id, limit, offset],
        ).fetchall()
        return [_map(r) for r in rows]

    def update(self, *_args: Any, **_kwargs: Any) -> None:
        raise OrganizationsError("AuditRepository is append-only; update is forbidden")

    def delete(self, *_args: Any, **_kwargs: Any) -> None:
        raise OrganizationsError("AuditRepository is append-only; delete is forbidden")
