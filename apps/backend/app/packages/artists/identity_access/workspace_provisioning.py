"""Spec 051 — hidden artist-workspace tenant provisioning.

An Artist Space is authorized by ``app_artist_membership`` but publishing and
every other organization-scoped domain need a real ``app_organization`` row.
This module provisions that backing tenant with
``organization_type='artist_workspace'`` so it stays out of ordinary
organization discovery, and migrates legacy ``organization_id = 0`` profiles
onto one.

Organization tables are only ever written through the Organizations
repositories (except ``compensate_created_workspace``, which deletes only rows
this call created and restores preexisting rows it mutated).

Provisioning runs in autocommit rather than one ``transactional()`` scope:
DuckDB's ART index rejects rewriting a pre-existing indexed row (both UPDATE
and DELETE + re-INSERT) while an explicit transaction is open, and this flow
has to touch existing organization/membership rows when it reuses a workspace.
Create vs reuse is therefore tracked explicitly: callers compensate only what
THIS call inserted or mutated, never by deleting a preexisting org/membership/role.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Optional

import duckdb

from app.core.logging import get_logger
from app.core.time_util import utc_now
from app.packages.artists.application.use_cases import _update_profile_row
from app.packages.artists.identity_access import ARTIST_WORKSPACE_TYPE, INDEPENDENT_ORG_ID
from app.packages.artists.identity_access.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.packages.organizations.domain.enums import MembershipStatus, OrganizationStatus
from app.packages.organizations.domain.errors import NotFoundError as OrgNotFoundError
from app.packages.organizations.infrastructure.repositories.authorization_repository import (
    AuthorizationRepository,
)
from app.packages.organizations.infrastructure.repositories.membership_repository import (
    MembershipRepository,
)
from app.packages.organizations.infrastructure.repositories.organization_repository import (
    OrganizationRepository,
)

logger = get_logger("voxmetrik.artists.workspace")

WORKSPACE_SLUG_PREFIX = "artist-ws"
_SLUG_BODY_MAX = 40

_MEMBERSHIP_COLS = (
    "id",
    "organization_id",
    "user_id",
    "status",
    "joined_at",
    "suspended_at",
    "left_at",
    "removed_at",
    "created_by",
    "created_at",
    "updated_at",
)

_MEMBER_ROLE_COLS = (
    "id",
    "member_id",
    "role_id",
    "status",
    "assigned_by",
    "assigned_at",
    "revoked_by",
    "revoked_at",
)


class WorkspaceProvisionError(ValidationError):
    """Backing tenant could not be created or reused."""

    code = "artist_workspace_provision_failed"


@dataclass(frozen=True)
class MembershipSnapshot:
    """Prior ``app_organization_member`` row before THIS call mutated it."""

    id: int
    organization_id: int
    user_id: int
    status: str
    joined_at: Any
    suspended_at: Any
    left_at: Any
    removed_at: Any
    created_by: Any
    created_at: Any
    updated_at: Any


@dataclass(frozen=True)
class MemberRoleSnapshot:
    """Prior ``app_member_role`` row before THIS call reactivated it."""

    id: int
    member_id: int
    role_id: int
    status: str
    assigned_by: Any
    assigned_at: Any
    revoked_by: Any
    revoked_at: Any


@dataclass(frozen=True)
class WorkspaceProvisionResult:
    """Outcome of one ``provision_artist_workspace`` call.

    ``created_*`` flags / ids are set only for rows inserted by THIS call.
    ``mutated_*`` hold prior-state snapshots for preexisting rows this call
    reactivated or otherwise changed. Compensation deletes only created rows
    and restores mutated rows — never deletes a preexisting membership/role/org.
    """

    organization_id: int
    created_organization: bool
    created_membership_id: Optional[int]
    created_role_assignment: bool
    created_member_role_id: Optional[int] = None
    mutated_membership: Optional[MembershipSnapshot] = None
    mutated_member_role: Optional[MemberRoleSnapshot] = None


@dataclass(frozen=True)
class _OwnerEnsureResult:
    membership_id: int
    created_membership_id: Optional[int]
    created_role_assignment: bool
    created_member_role_id: Optional[int]
    mutated_membership: Optional[MembershipSnapshot]
    mutated_member_role: Optional[MemberRoleSnapshot]


def workspace_slug(seed_key: str) -> str:
    """Deterministic slug for a seed key (profile/request identity, not display name)."""
    seed = (seed_key or "").strip().lower()
    if not seed:
        raise WorkspaceProvisionError("seed_key is required to provision a workspace")
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    body = re.sub(r"[^a-z0-9]+", "-", seed).strip("-")[:_SLUG_BODY_MAX].strip("-")
    return f"{WORKSPACE_SLUG_PREFIX}-{body}-{digest}" if body else f"{WORKSPACE_SLUG_PREFIX}-{digest}"


def _find_workspace(conn: duckdb.DuckDBPyConnection, slug: str):
    try:
        return OrganizationRepository(conn).get_by_slug(slug)
    except OrgNotFoundError:
        return None


def _membership_snapshot(
    conn: duckdb.DuckDBPyConnection, membership_id: int
) -> MembershipSnapshot:
    row = conn.execute(
        f"SELECT {', '.join(_MEMBERSHIP_COLS)} FROM app_organization_member WHERE id = ?",
        [membership_id],
    ).fetchone()
    if not row:
        raise WorkspaceProvisionError(f"membership id={membership_id} vanished")
    data = dict(zip(_MEMBERSHIP_COLS, row))
    return MembershipSnapshot(**data)


def _restore_membership_snapshot(
    conn: duckdb.DuckDBPyConnection, snap: MembershipSnapshot
) -> None:
    """Restore a preexisting membership exactly; never DELETE it."""
    conn.execute(
        """
        UPDATE app_organization_member
        SET status = ?,
            joined_at = ?,
            suspended_at = ?,
            left_at = ?,
            removed_at = ?,
            created_by = ?,
            created_at = ?,
            updated_at = ?
        WHERE id = ? AND organization_id = ? AND user_id = ?
        """,
        [
            snap.status,
            snap.joined_at,
            snap.suspended_at,
            snap.left_at,
            snap.removed_at,
            snap.created_by,
            snap.created_at,
            snap.updated_at,
            snap.id,
            snap.organization_id,
            snap.user_id,
        ],
    )


def _restore_member_role_snapshot(
    conn: duckdb.DuckDBPyConnection, snap: MemberRoleSnapshot
) -> None:
    """Restore a preexisting owner-role assignment exactly; never DELETE it."""
    conn.execute(
        """
        UPDATE app_member_role
        SET status = ?,
            assigned_by = ?,
            assigned_at = ?,
            revoked_by = ?,
            revoked_at = ?
        WHERE id = ? AND member_id = ? AND role_id = ?
        """,
        [
            snap.status,
            snap.assigned_by,
            snap.assigned_at,
            snap.revoked_by,
            snap.revoked_at,
            snap.id,
            snap.member_id,
            snap.role_id,
        ],
    )


def _reactivate_membership(
    conn: duckdb.DuckDBPyConnection, *, membership_id: int, organization_id: int
) -> MembershipSnapshot:
    """Capture prior state, then mark the preexisting membership active."""
    prior = _membership_snapshot(conn, membership_id)
    now = utc_now()
    conn.execute(
        """
        UPDATE app_organization_member
        SET status = ?,
            suspended_at = NULL,
            left_at = NULL,
            removed_at = NULL,
            updated_at = ?
        WHERE id = ? AND organization_id = ?
        """,
        [MembershipStatus.ACTIVE.value, now, membership_id, organization_id],
    )
    return prior


def _ensure_owner_membership(
    conn: duckdb.DuckDBPyConnection, *, organization_id: int, owner_user_id: int
) -> _OwnerEnsureResult:
    members = MembershipRepository(conn)
    auth = AuthorizationRepository(conn)
    created_membership_id: Optional[int] = None
    created_member_role_id: Optional[int] = None
    mutated_membership: Optional[MembershipSnapshot] = None
    mutated_member_role: Optional[MemberRoleSnapshot] = None
    try:
        membership = members.get_by_org_and_user(organization_id, owner_user_id)
        if membership is None:
            membership = members.create(
                organization_id=organization_id,
                user_id=owner_user_id,
                created_by=owner_user_id,
            )
            created_membership_id = int(membership.id)
        elif membership.status != MembershipStatus.ACTIVE.value:
            mutated_membership = _reactivate_membership(
                conn, membership_id=int(membership.id), organization_id=organization_id
            )
            membership = members.get_by_id_in_organization(
                int(membership.id), organization_id
            )

        owner_role_id = auth.get_role_id_by_code("owner")
        if owner_role_id is None:
            raise WorkspaceProvisionError(
                "owner role missing from the business role catalog"
            )

        prior = conn.execute(
            f"""
            SELECT {', '.join(_MEMBER_ROLE_COLS)} FROM app_member_role
            WHERE member_id = ? AND role_id = ?
            """,
            [membership.id, owner_role_id],
        ).fetchone()
        if prior is not None:
            prior_snap = MemberRoleSnapshot(**dict(zip(_MEMBER_ROLE_COLS, prior)))
            if prior_snap.status != "active":
                mutated_member_role = prior_snap
        assigned = auth.assign_member_role(
            member_id=membership.id,
            role_id=owner_role_id,
            assigned_by=owner_user_id,
            organization_id=organization_id,
        )
        created_role = prior is None
        if created_role:
            created_member_role_id = int(assigned.id)
        return _OwnerEnsureResult(
            membership_id=int(membership.id),
            created_membership_id=created_membership_id,
            created_role_assignment=created_role,
            created_member_role_id=created_member_role_id,
            mutated_membership=mutated_membership,
            mutated_member_role=mutated_member_role,
        )
    except Exception:
        compensate_created_workspace(
            conn,
            organization_id=organization_id,
            created_organization=False,
            created_membership_id=created_membership_id,
            created_role_assignment=created_member_role_id is not None,
            created_member_role_id=created_member_role_id,
            mutated_membership=mutated_membership,
            mutated_member_role=mutated_member_role,
        )
        raise


def compensate_created_workspace(
    conn: duckdb.DuckDBPyConnection,
    *,
    organization_id: int,
    created_organization: bool,
    created_membership_id: Optional[int] = None,
    created_role_assignment: bool = False,
    created_member_role_id: Optional[int] = None,
    mutated_membership: Optional[MembershipSnapshot] = None,
    mutated_member_role: Optional[MemberRoleSnapshot] = None,
) -> None:
    """Undo only what THIS provisioning call inserted or mutated.

    Restores preexisting membership / owner-role rows from snapshots.
    Deletes only rows this call inserted. Never deletes a reused organization
    or a preexisting membership/role. Safe as a no-op and idempotent.
    """
    if mutated_member_role is not None:
        _restore_member_role_snapshot(conn, mutated_member_role)
    elif created_role_assignment and created_member_role_id is not None:
        conn.execute(
            "DELETE FROM app_member_role WHERE id = ?", [created_member_role_id]
        )
    elif created_role_assignment and created_membership_id is not None:
        conn.execute(
            """
            DELETE FROM app_member_role
            WHERE member_id = ?
              AND role_id IN (
                  SELECT id FROM app_business_role WHERE code = 'owner'
              )
            """,
            [created_membership_id],
        )

    if mutated_membership is not None:
        _restore_membership_snapshot(conn, mutated_membership)
    elif created_membership_id is not None:
        conn.execute(
            "DELETE FROM app_organization_member WHERE id = ?",
            [created_membership_id],
        )

    if created_organization:
        conn.execute(
            """
            DELETE FROM app_member_role
            WHERE member_id IN (
                SELECT id FROM app_organization_member WHERE organization_id = ?
            )
            """,
            [organization_id],
        )
        conn.execute(
            "DELETE FROM app_organization_member WHERE organization_id = ?",
            [organization_id],
        )
        conn.execute(
            """
            DELETE FROM app_organization
            WHERE id = ? AND organization_type = ?
            """,
            [organization_id, ARTIST_WORKSPACE_TYPE],
        )


def _result_from_owner(
    organization_id: int,
    *,
    created_organization: bool,
    owner: _OwnerEnsureResult,
) -> WorkspaceProvisionResult:
    return WorkspaceProvisionResult(
        organization_id=int(organization_id),
        created_organization=created_organization,
        created_membership_id=owner.created_membership_id,
        created_role_assignment=owner.created_role_assignment,
        created_member_role_id=owner.created_member_role_id,
        mutated_membership=owner.mutated_membership,
        mutated_member_role=owner.mutated_member_role,
    )


def provision_artist_workspace(
    conn: duckdb.DuckDBPyConnection,
    *,
    display_name: str,
    owner_user_id: int,
    seed_key: str,
) -> WorkspaceProvisionResult:
    """Create or reuse the artist_workspace org + owner membership."""
    name = (display_name or "").strip()
    if not name:
        raise WorkspaceProvisionError("display_name is required to provision a workspace")
    slug = workspace_slug(seed_key)

    existing = _find_workspace(conn, slug)
    if existing is not None:
        if existing.organization_type != ARTIST_WORKSPACE_TYPE:
            raise WorkspaceProvisionError(
                f"slug {slug} is already used by a non artist_workspace organization"
            )
        owner = _ensure_owner_membership(
            conn, organization_id=existing.id, owner_user_id=owner_user_id
        )
        return _result_from_owner(
            int(existing.id), created_organization=False, owner=owner
        )

    orgs = OrganizationRepository(conn)
    org = orgs.create(
        display_name=name,
        slug=slug,
        organization_type=ARTIST_WORKSPACE_TYPE,
        created_by=owner_user_id,
        status=OrganizationStatus.PROVISIONING.value,
    )
    result = WorkspaceProvisionResult(
        organization_id=int(org.id),
        created_organization=True,
        created_membership_id=None,
        created_role_assignment=False,
        created_member_role_id=None,
    )
    try:
        owner = _ensure_owner_membership(
            conn, organization_id=org.id, owner_user_id=owner_user_id
        )
        result = _result_from_owner(
            int(org.id), created_organization=True, owner=owner
        )
        if AuthorizationRepository(conn).count_active_owners(org.id) < 1:
            raise WorkspaceProvisionError("artist workspace created without an active owner")
        orgs.update_status(org.id, OrganizationStatus.ACTIVE.value)
    except Exception:
        compensate_created_workspace(
            conn,
            organization_id=result.organization_id,
            created_organization=result.created_organization,
            created_membership_id=result.created_membership_id,
            created_role_assignment=result.created_role_assignment,
            created_member_role_id=result.created_member_role_id,
            mutated_membership=result.mutated_membership,
            mutated_member_role=result.mutated_member_role,
        )
        raise

    logger.info(
        "artist workspace provisioned organization_id=%s slug=%s owner_user_id=%s",
        org.id,
        slug,
        owner_user_id,
    )
    return result


def _profile_owner_user_id(conn: duckdb.DuckDBPyConnection, profile_id: int) -> int:
    row = conn.execute(
        """
        SELECT user_id FROM app_artist_membership
        WHERE artist_profile_id = ? AND role = 'owner' AND status = 'active'
        ORDER BY id
        LIMIT 1
        """,
        [profile_id],
    ).fetchone()
    if row:
        return int(row[0])
    created_by = conn.execute(
        "SELECT created_by FROM app_artist_profile WHERE id = ?", [profile_id]
    ).fetchone()
    if not created_by or created_by[0] is None:
        raise ConflictError(
            f"Artist profile {profile_id} has no active owner to back its workspace"
        )
    return int(created_by[0])


def _profile_head(conn: duckdb.DuckDBPyConnection, profile_id: int) -> tuple[int, str]:
    row = conn.execute(
        "SELECT organization_id, display_name FROM app_artist_profile WHERE id = ?",
        [profile_id],
    ).fetchone()
    if not row:
        raise NotFoundError(f"Artist profile {profile_id} not found")
    return int(row[0]), str(row[1])


def migrate_zero_backed_profile(conn: duckdb.DuckDBPyConnection, profile_id: int) -> int:
    """Idempotently move a sentinel-backed profile onto a workspace org."""
    organization_id, display_name = _profile_head(conn, profile_id)
    if organization_id != INDEPENDENT_ORG_ID:
        return organization_id

    owner_user_id = _profile_owner_user_id(conn, profile_id)
    workspace = provision_artist_workspace(
        conn,
        display_name=display_name,
        owner_user_id=owner_user_id,
        seed_key=f"profile:{profile_id}",
    )
    _update_profile_row(conn, profile_id, organization_id=workspace.organization_id)
    logger.info(
        "migrated artist profile_id=%s from sentinel org to organization_id=%s",
        profile_id,
        workspace.organization_id,
    )
    return workspace.organization_id


def resolve_publishing_organization(
    conn: duckdb.DuckDBPyConnection, profile_id: int
) -> int:
    """Organization that owns this artist's releases, migrating legacy rows on touch."""
    organization_id, _ = _profile_head(conn, profile_id)
    if organization_id == INDEPENDENT_ORG_ID:
        return migrate_zero_backed_profile(conn, profile_id)
    return organization_id


def is_artist_workspace(
    conn: duckdb.DuckDBPyConnection, organization_id: Optional[int]
) -> bool:
    if organization_id is None:
        return False
    row = conn.execute(
        "SELECT organization_type FROM app_organization WHERE id = ?",
        [organization_id],
    ).fetchone()
    return bool(row) and str(row[0]) == ARTIST_WORKSPACE_TYPE
