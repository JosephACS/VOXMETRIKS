"""User active-organization preference (not an authorization source)."""

from __future__ import annotations

from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.organizations.domain.entities import UserOrganizationPreference
from app.packages.organizations.domain.errors import ValidationError
from app.packages.organizations.infrastructure.repositories._helpers import (
    raise_persistence,
)


def _map(row: tuple[Any, ...]) -> UserOrganizationPreference:
    return UserOrganizationPreference(
        user_id=int(row[0]),
        active_organization_id=int(row[1]) if row[1] is not None else None,
        updated_at=row[2],
        updated_by=int(row[3]) if row[3] is not None else None,
    )


class PreferenceRepository:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def get_for_user(self, user_id: int) -> Optional[UserOrganizationPreference]:
        row = self._conn.execute(
            """
            SELECT user_id, active_organization_id, updated_at, updated_by
            FROM app_user_organization_preference
            WHERE user_id = ?
            """,
            [user_id],
        ).fetchone()
        return _map(row) if row else None

    def set_active_organization(
        self,
        user_id: int,
        organization_id: int,
        *,
        updated_by: Optional[int] = None,
    ) -> UserOrganizationPreference:
        user = self._conn.execute(
            "SELECT 1 FROM app_user WHERE id = ?", [user_id]
        ).fetchone()
        if not user:
            raise ValidationError(f"user id={user_id} does not exist")
        org = self._conn.execute(
            "SELECT 1 FROM app_organization WHERE id = ?", [organization_id]
        ).fetchone()
        if not org:
            raise ValidationError(f"organization id={organization_id} does not exist")

        now = utc_now()
        actor = updated_by if updated_by is not None else user_id
        existing = self.get_for_user(user_id)
        try:
            if existing is None:
                self._conn.execute(
                    """
                    INSERT INTO app_user_organization_preference (
                        user_id, active_organization_id, updated_at, updated_by
                    ) VALUES (?, ?, ?, ?)
                    """,
                    [user_id, organization_id, now, actor],
                )
            else:
                self._conn.execute(
                    """
                    UPDATE app_user_organization_preference
                    SET active_organization_id = ?, updated_at = ?, updated_by = ?
                    WHERE user_id = ?
                    """,
                    [organization_id, now, actor, user_id],
                )
        except Exception as exc:
            raise_persistence(exc, action="set active organization preference")
        pref = self.get_for_user(user_id)
        assert pref is not None
        return pref

    def clear_active_organization(
        self, user_id: int, *, updated_by: Optional[int] = None
    ) -> UserOrganizationPreference:
        now = utc_now()
        actor = updated_by if updated_by is not None else user_id
        existing = self.get_for_user(user_id)
        try:
            if existing is None:
                self._conn.execute(
                    """
                    INSERT INTO app_user_organization_preference (
                        user_id, active_organization_id, updated_at, updated_by
                    ) VALUES (?, NULL, ?, ?)
                    """,
                    [user_id, now, actor],
                )
            else:
                self._conn.execute(
                    """
                    UPDATE app_user_organization_preference
                    SET active_organization_id = NULL, updated_at = ?, updated_by = ?
                    WHERE user_id = ?
                    """,
                    [now, actor, user_id],
                )
        except Exception as exc:
            raise_persistence(exc, action="clear active organization preference")
        pref = self.get_for_user(user_id)
        assert pref is not None
        return pref
