"""Spec 051 — Platform review of independent (artist workspace) submissions.

Label/distributor releases keep their organization-scoped review queue. Releases
created inside a hidden ``artist_workspace`` tenant have no reviewing
organization, so Platform Ops reviews them here. All decisions delegate to
``CatalogPublishingUseCases`` — the state machine, self-review guard, history and
idempotent publish are unchanged.
"""

from __future__ import annotations

from typing import Any, Optional

import duckdb

from app.packages.artists.identity_access import ARTIST_WORKSPACE_TYPE
from app.packages.catalog_publishing.application.use_cases import (
    CatalogPublishingUseCases,
    _row_dict,
    _SUB_COLS,
)
from app.packages.catalog_publishing.domain.errors import NotFoundError

REVIEWABLE_STATUSES = (
    "submitted",
    "under_review",
    "changes_requested",
    "approved",
    "scheduled",
)


class PlatformCatalogReviewUseCases:
    """Independent-submission review queue, restricted to artist workspaces."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._publishing = CatalogPublishingUseCases(conn)

    def list(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        cols = ", ".join(f"s.{c}" for c in _SUB_COLS)
        sql = f"""
            SELECT {cols}
            FROM app_release_submission s
            INNER JOIN app_organization o ON o.id = s.organization_id
            WHERE o.organization_type = ?
        """
        params: list[Any] = [ARTIST_WORKSPACE_TYPE]
        if status:
            sql += " AND s.status = ?"
            params.append(status)
        else:
            placeholders = ", ".join("?" for _ in REVIEWABLE_STATUSES)
            sql += f" AND s.status IN ({placeholders})"
            params.extend(REVIEWABLE_STATUSES)
        sql += " ORDER BY s.updated_at DESC LIMIT ? OFFSET ?"
        params.extend([max(1, min(int(limit), 200)), max(0, int(offset))])
        return [_row_dict(_SUB_COLS, r) for r in self._conn.execute(sql, params).fetchall()]

    def _eligible(self, submission_id: int) -> dict[str, Any]:
        sub = self._publishing.get_submission(submission_id=submission_id)
        row = self._conn.execute(
            "SELECT organization_type FROM app_organization WHERE id = ?",
            [sub["organization_id"]],
        ).fetchone()
        if not row or str(row[0]) != ARTIST_WORKSPACE_TYPE:
            # Organization-backed releases are reviewed by their organization.
            raise NotFoundError(f"Submission {submission_id} not found")
        return sub

    def get_detail(self, *, submission_id: int) -> dict[str, Any]:
        sub = self._eligible(submission_id)
        return self._publishing.get_detail(
            submission_id=submission_id, organization_id=sub["organization_id"]
        )

    def request_changes(
        self, *, submission_id: int, actor_user_id: int, notes: str
    ) -> dict[str, Any]:
        sub = self._eligible(submission_id)
        return self._publishing.request_changes(
            submission_id=submission_id,
            organization_id=sub["organization_id"],
            actor_user_id=actor_user_id,
            notes=notes,
        )

    def approve(
        self, *, submission_id: int, actor_user_id: int, notes: Optional[str] = None
    ) -> dict[str, Any]:
        sub = self._eligible(submission_id)
        return self._publishing.approve(
            submission_id=submission_id,
            organization_id=sub["organization_id"],
            actor_user_id=actor_user_id,
            notes=notes,
        )

    def reject(
        self, *, submission_id: int, actor_user_id: int, reason: str
    ) -> dict[str, Any]:
        sub = self._eligible(submission_id)
        return self._publishing.reject(
            submission_id=submission_id,
            organization_id=sub["organization_id"],
            actor_user_id=actor_user_id,
            reason=reason,
        )

    def publish(
        self,
        *,
        submission_id: int,
        actor_user_id: int,
        idempotency_key: Optional[str] = None,
    ) -> dict[str, Any]:
        sub = self._eligible(submission_id)
        return self._publishing.publish(
            submission_id=submission_id,
            organization_id=sub["organization_id"],
            actor_user_id=actor_user_id,
            idempotency_key=idempotency_key,
        )
