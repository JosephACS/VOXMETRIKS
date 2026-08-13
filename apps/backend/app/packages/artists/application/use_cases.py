"""Artists consolidated use cases — Spec 020.

Covers: ArtistProfile lifecycle, organization links, manager assignments,
        team membership, external identifiers, status history, optional
        warehouse (dim_artista) linkage.

app_artist_profile (business record, organization-scoped) is always kept
distinct from dim_artista (analytics warehouse). LinkWarehouseArtist only
stores an optional, non-enforced reference — it never mutates the warehouse.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.artists.domain.entities import (
    ArtistAssignment,
    ArtistExternalIdentifier,
    ArtistOrganizationLink,
    ArtistProfile,
    ArtistStatusHistoryEntry,
    ArtistTeamMember,
)
from app.packages.artists.domain.errors import (
    ConflictError,
    DuplicateArtistError,
    ExternalIdentifierConflictError,
    InvalidTransitionError,
    NotFoundError,
    ValidationError,
    WarehouseArtistNotFoundError,
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    row = conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()
    return int(row[0])


def _now() -> datetime:
    return utc_now()


_PROFILE_ROW_COLS = (
    "id", "organization_id", "display_name", "legal_name", "normalized_name",
    "status", "warehouse_artist_id", "created_by", "created_at", "updated_at",
)


def _update_profile_row(conn: duckdb.DuckDBPyConnection, artist_id: int, **changes: Any) -> None:
    """Mutate a single app_artist_profile row via DELETE + re-INSERT (same id).

    DuckDB has a known limitation (see schema.py module docstring and
    https://duckdb.org/docs/sql/indexes) where, under certain connection
    open/close/reopen sequences against a persisted database file, a plain
    UPDATE on this table can raise a spurious PRIMARY KEY ConstraintException
    even though no duplicate row exists. INSERT does not trigger this, so
    profile mutations (status transitions, LinkWarehouseArtist,
    TransferArtistOrganization) are applied as an atomic delete + re-insert
    of the same row (id preserved) instead of UPDATE.
    """
    row = conn.execute(
        f"SELECT {', '.join(_PROFILE_ROW_COLS)} FROM app_artist_profile WHERE id = ?",
        [artist_id],
    ).fetchone()
    if row is None:
        raise NotFoundError(f"Artist profile {artist_id} not found")
    values = dict(zip(_PROFILE_ROW_COLS, row))
    values.update(changes)
    conn.execute("DELETE FROM app_artist_profile WHERE id = ?", [artist_id])
    conn.execute(
        f"INSERT INTO app_artist_profile ({', '.join(_PROFILE_ROW_COLS)}) "
        f"VALUES ({', '.join(['?'] * len(_PROFILE_ROW_COLS))})",
        [values[c] for c in _PROFILE_ROW_COLS],
    )


def normalize_artist_name(display_name: str) -> str:
    """Lowercase, strip accents, collapse whitespace for dedupe within an org."""
    value = unicodedata.normalize("NFKD", display_name)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.strip().lower()
    value = re.sub(r"\s+", " ", value)
    return value


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
            source="artists.use_case",
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


def _record_status_history(
    conn: duckdb.DuckDBPyConnection,
    *,
    artist_id: int,
    organization_id: int,
    from_status: Optional[str],
    to_status: str,
    reason: Optional[str],
    actor_user_id: Optional[int],
) -> None:
    now = _now()
    hid = _next_id(conn, "app_artist_status_history")
    conn.execute(
        f"INSERT INTO app_artist_status_history ({_HISTORY_COLS}) VALUES (?,?,?,?,?,?,?,?,?)",
        [hid, artist_id, organization_id, from_status, to_status, reason, actor_user_id, now, now],
    )


# ── Column lists ───────────────────────────────────────────────────────────────

_PROFILE_COLS = (
    "id, organization_id, display_name, legal_name, normalized_name, status, "
    "warehouse_artist_id, created_by, created_at, updated_at"
)

_ORG_LINK_COLS = (
    "id, artist_id, organization_id, relationship_role, is_primary, status, "
    "created_at, updated_at"
)

_ASSIGNMENT_COLS = (
    "id, artist_id, organization_id, user_id, role, status, assigned_at, "
    "ended_at, created_at, updated_at"
)

_TEAM_COLS = (
    "id, artist_id, organization_id, user_id, team_role, status, added_at, "
    "removed_at, created_at, updated_at"
)

_EXT_ID_COLS = (
    "id, artist_id, system_code, external_value, created_at, updated_at"
)

_HISTORY_COLS = (
    "id, artist_id, organization_id, from_status, to_status, reason, "
    "actor_user_id, at, created_at"
)


# ── Mappers ────────────────────────────────────────────────────────────────────


def _map_profile(r: tuple) -> ArtistProfile:
    return ArtistProfile(
        id=int(r[0]), organization_id=int(r[1]), display_name=str(r[2]),
        legal_name=r[3], normalized_name=str(r[4]), status=str(r[5]),
        warehouse_artist_id=int(r[6]) if r[6] is not None else None,
        created_by=int(r[7]) if r[7] is not None else None,
        created_at=r[8], updated_at=r[9],
    )


def _map_org_link(r: tuple) -> ArtistOrganizationLink:
    return ArtistOrganizationLink(
        id=int(r[0]), artist_id=int(r[1]), organization_id=int(r[2]),
        relationship_role=str(r[3]), is_primary=bool(r[4]), status=str(r[5]),
        created_at=r[6], updated_at=r[7],
    )


def _map_assignment(r: tuple) -> ArtistAssignment:
    return ArtistAssignment(
        id=int(r[0]), artist_id=int(r[1]), organization_id=int(r[2]),
        user_id=int(r[3]), role=str(r[4]), status=str(r[5]),
        assigned_at=r[6], ended_at=r[7], created_at=r[8], updated_at=r[9],
    )


def _map_team_member(r: tuple) -> ArtistTeamMember:
    return ArtistTeamMember(
        id=int(r[0]), artist_id=int(r[1]), organization_id=int(r[2]),
        user_id=int(r[3]), team_role=str(r[4]), status=str(r[5]),
        added_at=r[6], removed_at=r[7], created_at=r[8], updated_at=r[9],
    )


def _map_ext_id(r: tuple) -> ArtistExternalIdentifier:
    return ArtistExternalIdentifier(
        id=int(r[0]), artist_id=int(r[1]), system_code=str(r[2]),
        external_value=str(r[3]), created_at=r[4], updated_at=r[5],
    )


def _map_history(r: tuple) -> ArtistStatusHistoryEntry:
    return ArtistStatusHistoryEntry(
        id=int(r[0]), artist_id=int(r[1]), organization_id=int(r[2]),
        from_status=r[3], to_status=str(r[4]), reason=r[5],
        actor_user_id=int(r[6]) if r[6] is not None else None,
        at=r[7], created_at=r[8],
    )


_VALID_STATUSES = ("draft", "active", "inactive", "archived")

_ALLOWED_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "draft": ("active", "archived"),
    "active": ("inactive", "archived"),
    "inactive": ("active", "archived"),
    "archived": (),
}


# ── ArtistProfile Use Cases ────────────────────────────────────────────────────


class ArtistProfileUseCases:
    """CreateArtistProfile, ActivateArtist, DeactivateArtist, ArchiveArtist,
    LinkWarehouseArtist, TransferArtistOrganization, ListArtists, GetArtist."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        organization_id: int,
        display_name: str,
        legal_name: Optional[str] = None,
        warehouse_artist_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> ArtistProfile:
        name = (display_name or "").strip()
        if not name:
            raise ValidationError("display_name is required")
        if len(name) > 200:
            raise ValidationError("display_name must be at most 200 characters")

        normalized = normalize_artist_name(name)
        if not normalized:
            raise ValidationError("display_name must contain visible characters")

        existing = self._conn.execute(
            "SELECT 1 FROM app_artist_profile WHERE organization_id = ? AND normalized_name = ?",
            [organization_id, normalized],
        ).fetchone()
        if existing:
            raise DuplicateArtistError(
                f"Artist '{display_name}' already exists in organization {organization_id}"
            )

        if warehouse_artist_id is not None:
            self._assert_warehouse_artist_exists(warehouse_artist_id)

        now = _now()
        aid = _next_id(self._conn, "app_artist_profile")
        self._conn.execute(
            f"""
            INSERT INTO app_artist_profile ({_PROFILE_COLS})
            VALUES (?,?,?,?,?,'draft',?,?,?,?)
            """,
            [aid, organization_id, name, legal_name, normalized,
             warehouse_artist_id, actor_user_id, now, now],
        )
        # Primary organization link
        link_id = _next_id(self._conn, "app_artist_organization")
        self._conn.execute(
            f"INSERT INTO app_artist_organization ({_ORG_LINK_COLS}) VALUES (?,?,?,'primary',TRUE,'active',?,?)",
            [link_id, aid, organization_id, now, now],
        )
        _record_status_history(
            self._conn, artist_id=aid, organization_id=organization_id,
            from_status=None, to_status="draft", reason="created",
            actor_user_id=actor_user_id,
        )
        profile = self._get_or_raise(aid)
        _audit(
            self._conn, action="artist_profile.created",
            target_type="artist_profile", target_id=str(aid),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"display_name": display_name, "status": "draft"},
            request_id=request_id,
        )
        return profile

    def activate(
        self,
        artist_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> ArtistProfile:
        return self._transition(
            artist_id, to_status="active", actor_user_id=actor_user_id,
            organization_id=organization_id, reason=reason, request_id=request_id,
        )

    def deactivate(
        self,
        artist_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> ArtistProfile:
        return self._transition(
            artist_id, to_status="inactive", actor_user_id=actor_user_id,
            organization_id=organization_id, reason=reason, request_id=request_id,
        )

    def archive(
        self,
        artist_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> ArtistProfile:
        return self._transition(
            artist_id, to_status="archived", actor_user_id=actor_user_id,
            organization_id=organization_id, reason=reason, request_id=request_id,
        )

    def link_warehouse_artist(
        self,
        artist_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        warehouse_artist_id: int,
        request_id: Optional[str] = None,
    ) -> ArtistProfile:
        """LinkWarehouseArtist — optional, non-destructive reference to dim_artista."""
        artist = self._get_or_raise_for_org(artist_id, organization_id)
        self._assert_warehouse_artist_exists(warehouse_artist_id)

        now = _now()
        _update_profile_row(
            self._conn, artist_id,
            warehouse_artist_id=warehouse_artist_id, updated_at=now,
        )
        _audit(
            self._conn, action="artist_profile.warehouse_linked",
            target_type="artist_profile", target_id=str(artist_id),
            actor_user_id=actor_user_id, organization_id=organization_id,
            previous_values={"warehouse_artist_id": artist.warehouse_artist_id},
            new_values={"warehouse_artist_id": warehouse_artist_id},
            request_id=request_id,
        )
        return self._get_or_raise(artist_id)

    def transfer_organization(
        self,
        artist_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        target_organization_id: int,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> ArtistProfile:
        """TransferArtistOrganization — audited-only move of primary ownership.

        Does not require target org membership validation here (out of scope);
        it always writes a full audit trail with previous/new organization_id.
        """
        artist = self._get_or_raise_for_org(artist_id, organization_id)
        if target_organization_id == organization_id:
            raise ValidationError("target_organization_id must differ from current organization")

        now = _now()
        _update_profile_row(
            self._conn, artist_id,
            organization_id=target_organization_id, updated_at=now,
        )
        # End old primary link, create new primary link
        self._conn.execute(
            "UPDATE app_artist_organization SET status = 'ended', updated_at = ? "
            "WHERE artist_id = ? AND organization_id = ? AND is_primary = TRUE",
            [now, artist_id, organization_id],
        )
        link_id = _next_id(self._conn, "app_artist_organization")
        self._conn.execute(
            f"INSERT INTO app_artist_organization ({_ORG_LINK_COLS}) VALUES (?,?,?,'primary',TRUE,'active',?,?)",
            [link_id, artist_id, target_organization_id, now, now],
        )
        _audit(
            self._conn, action="artist_profile.transferred",
            target_type="artist_profile", target_id=str(artist_id),
            actor_user_id=actor_user_id, organization_id=organization_id,
            previous_values={"organization_id": organization_id},
            new_values={"organization_id": target_organization_id},
            reason=reason,
            request_id=request_id,
        )
        return self._get_or_raise(artist_id)

    def list(
        self,
        *,
        organization_id: int,
        status: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[ArtistProfile], int]:
        conditions = ["organization_id = ?"]
        params: list[Any] = [organization_id]
        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        where = " AND ".join(conditions)
        total = int(
            self._conn.execute(
                f"SELECT COUNT(*) FROM app_artist_profile WHERE {where}", params
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_PROFILE_COLS} FROM app_artist_profile WHERE {where} "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [_map_profile(r) for r in rows], total

    def get(self, artist_id: int, *, organization_id: int) -> ArtistProfile:
        return self._get_or_raise_for_org(artist_id, organization_id)

    def _transition(
        self,
        artist_id: int,
        *,
        to_status: str,
        actor_user_id: int,
        organization_id: int,
        reason: Optional[str],
        request_id: Optional[str],
    ) -> ArtistProfile:
        artist = self._get_or_raise_for_org(artist_id, organization_id)
        allowed = _ALLOWED_TRANSITIONS.get(artist.status, ())
        if to_status not in allowed:
            raise InvalidTransitionError(
                f"Cannot transition artist from {artist.status} to {to_status}"
            )
        now = _now()
        _update_profile_row(
            self._conn, artist_id,
            status=to_status, updated_at=now,
        )
        _record_status_history(
            self._conn, artist_id=artist_id, organization_id=organization_id,
            from_status=artist.status, to_status=to_status, reason=reason,
            actor_user_id=actor_user_id,
        )
        _audit(
            self._conn, action=f"artist_profile.{to_status}",
            target_type="artist_profile", target_id=str(artist_id),
            actor_user_id=actor_user_id, organization_id=organization_id,
            previous_values={"status": artist.status},
            new_values={"status": to_status},
            reason=reason,
            request_id=request_id,
        )
        return self._get_or_raise(artist_id)

    def _assert_warehouse_artist_exists(self, warehouse_artist_id: int) -> None:
        try:
            row = self._conn.execute(
                "SELECT 1 FROM dim_artista WHERE id_artista = ?", [warehouse_artist_id]
            ).fetchone()
        except Exception:
            # dim_artista may not exist in a minimal test database — treat as not found.
            row = None
        if not row:
            raise WarehouseArtistNotFoundError(
                f"dim_artista.id_artista={warehouse_artist_id} not found"
            )

    def _get_or_raise(self, artist_id: int) -> ArtistProfile:
        row = self._conn.execute(
            f"SELECT {_PROFILE_COLS} FROM app_artist_profile WHERE id = ?", [artist_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"artist_profile id={artist_id}")
        return _map_profile(row)

    def _get_or_raise_for_org(self, artist_id: int, organization_id: int) -> ArtistProfile:
        row = self._conn.execute(
            f"SELECT {_PROFILE_COLS} FROM app_artist_profile WHERE id = ? AND organization_id = ?",
            [artist_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"artist_profile id={artist_id}")
        return _map_profile(row)


# ── ArtistOrganization Use Cases ───────────────────────────────────────────────


class ArtistOrganizationUseCases:
    """LinkOrganization — secondary org relationships beyond primary ownership."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def link(
        self,
        artist_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        target_organization_id: int,
        relationship_role: str = "secondary",
        request_id: Optional[str] = None,
    ) -> ArtistOrganizationLink:
        ArtistProfileUseCases(self._conn).get(artist_id, organization_id=organization_id)

        if relationship_role not in ("secondary", "licensed", "partner"):
            raise ValidationError("relationship_role must be secondary, licensed, or partner")

        existing = self._conn.execute(
            "SELECT 1 FROM app_artist_organization WHERE artist_id = ? AND organization_id = ?",
            [artist_id, target_organization_id],
        ).fetchone()
        if existing:
            raise ConflictError(
                f"Artist {artist_id} already linked to organization {target_organization_id}"
            )

        now = _now()
        link_id = _next_id(self._conn, "app_artist_organization")
        self._conn.execute(
            f"INSERT INTO app_artist_organization ({_ORG_LINK_COLS}) VALUES (?,?,?,?,FALSE,'active',?,?)",
            [link_id, artist_id, target_organization_id, relationship_role, now, now],
        )
        _audit(
            self._conn, action="artist_organization.linked",
            target_type="artist_organization", target_id=str(link_id),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"artist_id": artist_id, "organization_id": target_organization_id},
            request_id=request_id,
        )
        row = self._conn.execute(
            f"SELECT {_ORG_LINK_COLS} FROM app_artist_organization WHERE id = ?", [link_id]
        ).fetchone()
        return _map_org_link(row)

    def list_for_artist(self, artist_id: int) -> list[ArtistOrganizationLink]:
        rows = self._conn.execute(
            f"SELECT {_ORG_LINK_COLS} FROM app_artist_organization WHERE artist_id = ? ORDER BY id ASC",
            [artist_id],
        ).fetchall()
        return [_map_org_link(r) for r in rows]


# ── ArtistAssignment Use Cases ─────────────────────────────────────────────────


class ArtistAssignmentUseCases:
    """AssignManager, EndAssignment."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def assign_manager(
        self,
        artist_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        user_id: int,
        role: str = "manager",
        request_id: Optional[str] = None,
    ) -> ArtistAssignment:
        ArtistProfileUseCases(self._conn).get(artist_id, organization_id=organization_id)

        existing = self._conn.execute(
            "SELECT id FROM app_artist_assignment WHERE artist_id = ? AND user_id = ? "
            "AND role = ? AND status = 'active'",
            [artist_id, user_id, role],
        ).fetchone()
        if existing:
            raise ConflictError(
                f"User {user_id} already has active {role} assignment for artist {artist_id}"
            )

        now = _now()
        aid = _next_id(self._conn, "app_artist_assignment")
        self._conn.execute(
            f"INSERT INTO app_artist_assignment ({_ASSIGNMENT_COLS}) VALUES (?,?,?,?,?,'active',?,NULL,?,?)",
            [aid, artist_id, organization_id, user_id, role, now, now, now],
        )
        _audit(
            self._conn, action="artist_assignment.created",
            target_type="artist_assignment", target_id=str(aid),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"artist_id": artist_id, "user_id": user_id, "role": role},
            request_id=request_id,
        )
        row = self._conn.execute(
            f"SELECT {_ASSIGNMENT_COLS} FROM app_artist_assignment WHERE id = ?", [aid]
        ).fetchone()
        return _map_assignment(row)

    def end_assignment(
        self,
        assignment_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        request_id: Optional[str] = None,
    ) -> ArtistAssignment:
        row = self._conn.execute(
            f"SELECT {_ASSIGNMENT_COLS} FROM app_artist_assignment WHERE id = ? AND organization_id = ?",
            [assignment_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"artist_assignment id={assignment_id}")
        assignment = _map_assignment(row)
        if assignment.status != "active":
            raise InvalidTransitionError("Assignment is already ended")

        now = _now()
        self._conn.execute(
            "UPDATE app_artist_assignment SET status='ended', ended_at=?, updated_at=? WHERE id=?",
            [now, now, assignment_id],
        )
        _audit(
            self._conn, action="artist_assignment.ended",
            target_type="artist_assignment", target_id=str(assignment_id),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"status": "ended"},
            request_id=request_id,
        )
        row = self._conn.execute(
            f"SELECT {_ASSIGNMENT_COLS} FROM app_artist_assignment WHERE id = ?", [assignment_id]
        ).fetchone()
        return _map_assignment(row)

    def list_for_artist(self, artist_id: int) -> list[ArtistAssignment]:
        rows = self._conn.execute(
            f"SELECT {_ASSIGNMENT_COLS} FROM app_artist_assignment WHERE artist_id = ? ORDER BY id ASC",
            [artist_id],
        ).fetchall()
        return [_map_assignment(r) for r in rows]


# ── ArtistTeamMember Use Cases ─────────────────────────────────────────────────


class ArtistTeamUseCases:
    """AddTeamMember, RemoveTeamMember."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def add_member(
        self,
        artist_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        user_id: int,
        team_role: str,
        request_id: Optional[str] = None,
    ) -> ArtistTeamMember:
        ArtistProfileUseCases(self._conn).get(artist_id, organization_id=organization_id)
        if not team_role or not team_role.strip():
            raise ValidationError("team_role is required")

        existing = self._conn.execute(
            "SELECT id FROM app_artist_team_member WHERE artist_id = ? AND user_id = ? "
            "AND status = 'active'",
            [artist_id, user_id],
        ).fetchone()
        if existing:
            raise ConflictError(
                f"User {user_id} is already an active team member for artist {artist_id}"
            )

        now = _now()
        tid = _next_id(self._conn, "app_artist_team_member")
        self._conn.execute(
            f"INSERT INTO app_artist_team_member ({_TEAM_COLS}) VALUES (?,?,?,?,?,'active',?,NULL,?,?)",
            [tid, artist_id, organization_id, user_id, team_role.strip(), now, now, now],
        )
        _audit(
            self._conn, action="artist_team_member.added",
            target_type="artist_team_member", target_id=str(tid),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"artist_id": artist_id, "user_id": user_id, "team_role": team_role},
            request_id=request_id,
        )
        row = self._conn.execute(
            f"SELECT {_TEAM_COLS} FROM app_artist_team_member WHERE id = ?", [tid]
        ).fetchone()
        return _map_team_member(row)

    def remove_member(
        self,
        team_member_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        request_id: Optional[str] = None,
    ) -> ArtistTeamMember:
        row = self._conn.execute(
            f"SELECT {_TEAM_COLS} FROM app_artist_team_member WHERE id = ? AND organization_id = ?",
            [team_member_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"artist_team_member id={team_member_id}")
        member = _map_team_member(row)
        if member.status != "active":
            raise InvalidTransitionError("Team member is already removed")

        now = _now()
        self._conn.execute(
            "UPDATE app_artist_team_member SET status='removed', removed_at=?, updated_at=? WHERE id=?",
            [now, now, team_member_id],
        )
        _audit(
            self._conn, action="artist_team_member.removed",
            target_type="artist_team_member", target_id=str(team_member_id),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"status": "removed"},
            request_id=request_id,
        )
        row = self._conn.execute(
            f"SELECT {_TEAM_COLS} FROM app_artist_team_member WHERE id = ?", [team_member_id]
        ).fetchone()
        return _map_team_member(row)

    def list_for_artist(self, artist_id: int) -> list[ArtistTeamMember]:
        rows = self._conn.execute(
            f"SELECT {_TEAM_COLS} FROM app_artist_team_member WHERE artist_id = ? ORDER BY id ASC",
            [artist_id],
        ).fetchall()
        return [_map_team_member(r) for r in rows]


# ── ArtistExternalIdentifier Use Cases ─────────────────────────────────────────


class ArtistExternalIdentifierUseCases:
    """SetExternalIdentifier — upsert by (artist_id, system_code)."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def set_identifier(
        self,
        artist_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        system_code: str,
        external_value: str,
        request_id: Optional[str] = None,
    ) -> ArtistExternalIdentifier:
        ArtistProfileUseCases(self._conn).get(artist_id, organization_id=organization_id)
        if not system_code or not system_code.strip():
            raise ValidationError("system_code is required")
        if not external_value or not external_value.strip():
            raise ValidationError("external_value is required")

        now = _now()
        existing = self._conn.execute(
            f"SELECT {_EXT_ID_COLS} FROM app_artist_external_identifier "
            "WHERE artist_id = ? AND system_code = ?",
            [artist_id, system_code.strip()],
        ).fetchone()
        if existing:
            eid = int(existing[0])
            self._conn.execute(
                "UPDATE app_artist_external_identifier SET external_value = ?, updated_at = ? WHERE id = ?",
                [external_value.strip(), now, eid],
            )
        else:
            eid = _next_id(self._conn, "app_artist_external_identifier")
            try:
                self._conn.execute(
                    f"INSERT INTO app_artist_external_identifier ({_EXT_ID_COLS}) VALUES (?,?,?,?,?,?)",
                    [eid, artist_id, system_code.strip(), external_value.strip(), now, now],
                )
            except Exception as exc:
                raise ExternalIdentifierConflictError(
                    f"system_code {system_code!r} already exists for artist {artist_id}"
                ) from exc

        _audit(
            self._conn, action="artist_external_identifier.set",
            target_type="artist_external_identifier", target_id=str(eid),
            actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"system_code": system_code, "external_value": external_value},
            request_id=request_id,
        )
        row = self._conn.execute(
            f"SELECT {_EXT_ID_COLS} FROM app_artist_external_identifier WHERE id = ?", [eid]
        ).fetchone()
        return _map_ext_id(row)

    def list_for_artist(self, artist_id: int) -> list[ArtistExternalIdentifier]:
        rows = self._conn.execute(
            f"SELECT {_EXT_ID_COLS} FROM app_artist_external_identifier WHERE artist_id = ? ORDER BY id ASC",
            [artist_id],
        ).fetchall()
        return [_map_ext_id(r) for r in rows]


# ── ArtistStatusHistory Use Cases ──────────────────────────────────────────────


class ArtistHistoryUseCases:
    """GetHistory — read-only, append-only status trail."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def get_history(self, artist_id: int, *, organization_id: int) -> list[ArtistStatusHistoryEntry]:
        ArtistProfileUseCases(self._conn).get(artist_id, organization_id=organization_id)
        rows = self._conn.execute(
            f"SELECT {_HISTORY_COLS} FROM app_artist_status_history "
            "WHERE artist_id = ? ORDER BY at ASC, id ASC",
            [artist_id],
        ).fetchall()
        return [_map_history(r) for r in rows]
