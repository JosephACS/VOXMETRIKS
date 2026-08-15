"""Spec 046 — Artist Space use cases (membership, access requests, invitations)."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.parse import urlparse

import duckdb

from app.core.time_util import utc_now
from app.packages.artists.identity_access import (
    ALL_ROLES,
    INDEPENDENT_ORG_ID,
    INVITE_ROLES,
    RELATIONSHIP_TYPES,
    REQUEST_TYPES,
    permissions_for_role,
    role_has_permission,
)
from app.packages.artists.identity_access.errors import (
    ConflictError,
    EvidenceRequired,
    InvitationAlreadyUsed,
    InvitationExpired,
    InvitationRevoked,
    NotFoundError,
    PermissionDenied,
    ValidationError,
)
from app.packages.artists.identity_access.workspace_provisioning import (
    WorkspaceProvisionError,
    WorkspaceProvisionResult,
    compensate_created_workspace,
    migrate_zero_backed_profile,
    provision_artist_workspace,
)
from app.packages.artists.application.use_cases import _update_profile_row
from app.packages.identity.services.user_service import _fetch_user
from app.packages.organizations.domain.invitation_token import (
    generate_invitation_token,
    hash_invitation_token,
)
from app.packages.organizations.domain.rules import normalize_email
from app.packages.platform_rbac.infrastructure import repository as rbac_repo

DEFAULT_INVITE_TTL_DAYS = 14


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    row = conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()
    return int(row[0])


def _now() -> datetime:
    return utc_now()


def _normalize_name(name: str) -> str:
    nfkd = unicodedata.normalize("NFKD", name.strip().lower())
    ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", ascii_only).strip()


def is_platform_admin(conn: duckdb.DuckDBPyConnection, user_id: int) -> bool:
    """Mirror FE platformAdminGuard: identity admin OR CRM platform_admin."""
    user = _fetch_user(conn, user_id)
    if user and (user.get("role") or "").lower() == "admin":
        return True
    roles = rbac_repo.list_user_platform_roles(conn, user_id)
    return "platform_admin" in roles


_PROFILE_COLS = (
    "id",
    "organization_id",
    "display_name",
    "legal_name",
    "normalized_name",
    "status",
    "warehouse_artist_id",
    "created_by",
    "created_at",
    "updated_at",
    # Spec 051 additive public metadata
    "bio",
    "country_code",
    "primary_genre",
    "website_url",
    "image_url",
)

_REQUEST_COLS = (
    "id",
    "applicant_user_id",
    "request_type",
    "target_artist_profile_id",
    "warehouse_artist_id",
    "proposed_display_name",
    "proposed_role",
    "status",
    "created_at",
    "reviewed_at",
    "reviewer_user_id",
    "rejection_reason",
    # Spec 051 additive evidence
    "relationship_type",
    "evidence_url",
    "evidence_note",
)

_REQUEST_SELECT = ", ".join(_REQUEST_COLS)


def _get_profile(conn: duckdb.DuckDBPyConnection, artist_profile_id: int) -> dict[str, Any]:
    row = conn.execute(
        f"SELECT {', '.join(_PROFILE_COLS)} FROM app_artist_profile WHERE id = ?",
        [artist_profile_id],
    ).fetchone()
    if not row:
        raise NotFoundError(f"Artist profile {artist_profile_id} not found")
    data = dict(zip(_PROFILE_COLS, row))
    return {
        **data,
        "id": int(data["id"]),
        "organization_id": int(data["organization_id"]),
        "display_name": str(data["display_name"]),
        "normalized_name": str(data["normalized_name"]),
        "status": str(data["status"]),
        "warehouse_artist_id": (
            int(data["warehouse_artist_id"])
            if data["warehouse_artist_id"] is not None
            else None
        ),
        "created_by": int(data["created_by"]) if data["created_by"] is not None else None,
    }


def _active_membership(
    conn: duckdb.DuckDBPyConnection, *, artist_profile_id: int, user_id: int
) -> Optional[dict[str, Any]]:
    row = conn.execute(
        """
        SELECT id, artist_profile_id, user_id, role, status, created_at, updated_at, revoked_at
        FROM app_artist_membership
        WHERE artist_profile_id = ? AND user_id = ? AND status = 'active'
        LIMIT 1
        """,
        [artist_profile_id, user_id],
    ).fetchone()
    if not row:
        return None
    return _membership_dict(row)


def _membership_dict(row: tuple) -> dict[str, Any]:
    return {
        "id": int(row[0]),
        "artist_profile_id": int(row[1]),
        "user_id": int(row[2]),
        "role": str(row[3]),
        "status": str(row[4]),
        "created_at": row[5],
        "updated_at": row[6],
        "revoked_at": row[7],
    }


def _require_membership(
    conn: duckdb.DuckDBPyConnection,
    *,
    artist_profile_id: int,
    user_id: int,
    permission: Optional[str] = None,
) -> dict[str, Any]:
    m = _active_membership(conn, artist_profile_id=artist_profile_id, user_id=user_id)
    if m is None:
        raise PermissionDenied("No active artist membership")
    if permission and not role_has_permission(m["role"], permission):
        raise PermissionDenied(f"Missing permission: {permission}")
    return m


def _count_active_owners(conn: duckdb.DuckDBPyConnection, artist_profile_id: int) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) FROM app_artist_membership
        WHERE artist_profile_id = ? AND role = 'owner' AND status = 'active'
        """,
        [artist_profile_id],
    ).fetchone()
    return int(row[0]) if row else 0


def _find_profile_by_warehouse(
    conn: duckdb.DuckDBPyConnection, warehouse_artist_id: int
) -> Optional[dict[str, Any]]:
    row = conn.execute(
        "SELECT id FROM app_artist_profile WHERE warehouse_artist_id = ? LIMIT 1",
        [warehouse_artist_id],
    ).fetchone()
    if not row:
        return None
    return _get_profile(conn, int(row[0]))


def _table_exists(conn: duckdb.DuckDBPyConnection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_name = ? LIMIT 1",
        [table],
    ).fetchone()
    return row is not None


def _warehouse_exists(conn: duckdb.DuckDBPyConnection, warehouse_artist_id: int) -> bool:
    if not _table_exists(conn, "dim_artista"):
        return False
    row = conn.execute(
        "SELECT 1 FROM dim_artista WHERE id_artista = ? LIMIT 1",
        [warehouse_artist_id],
    ).fetchone()
    return row is not None


def _warehouse_name(conn: duckdb.DuckDBPyConnection, warehouse_artist_id: int) -> Optional[str]:
    if not _table_exists(conn, "dim_artista"):
        return None
    row = conn.execute(
        "SELECT nombre_artista FROM dim_artista WHERE id_artista = ?",
        [warehouse_artist_id],
    ).fetchone()
    return str(row[0]) if row else None


def _validate_http_url(value: str, *, field: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValidationError(f"{field} must be an absolute http(s) URL")
    if len(value) > 500:
        raise ValidationError(f"{field} must be at most 500 characters")
    return value


def _list_external_identifiers(
    conn: duckdb.DuckDBPyConnection, artist_profile_id: int
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, system_code, external_value
        FROM app_artist_external_identifier
        WHERE artist_id = ?
        ORDER BY system_code
        """,
        [artist_profile_id],
    ).fetchall()
    return [
        {"id": int(r[0]), "system_code": str(r[1]), "external_value": str(r[2])}
        for r in rows
    ]


def _normalize_external_identifiers(entries: list[dict[str, Any]]) -> dict[str, str]:
    """Validate the requested set before anything is written."""
    normalized: dict[str, str] = {}
    for entry in entries:
        system_code = str(entry.get("system_code") or "").strip().lower()
        external_value = str(entry.get("external_value") or "").strip()
        if not system_code or not external_value:
            raise ValidationError(
                "external identifiers require system_code and external_value"
            )
        if len(system_code) > 40 or len(external_value) > 200:
            raise ValidationError("external identifier value is too long")
        if system_code in normalized:
            raise ConflictError(f"Duplicate external identifier system: {system_code}")
        normalized[system_code] = external_value
    return normalized


def _replace_external_identifiers(
    conn: duckdb.DuckDBPyConnection,
    artist_profile_id: int,
    normalized: dict[str, str],
) -> None:
    """Replace the whole set for one profile (autocommit, see DuckDB note)."""
    now = _now()
    conn.execute(
        "DELETE FROM app_artist_external_identifier WHERE artist_id = ?",
        [artist_profile_id],
    )
    for system_code, external_value in normalized.items():
        eid = _next_id(conn, "app_artist_external_identifier")
        conn.execute(
            """
            INSERT INTO app_artist_external_identifier
                (id, artist_id, system_code, external_value, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [eid, artist_profile_id, system_code, external_value, now, now],
        )


def _search_warehouse_artists(
    conn: duckdb.DuckDBPyConnection, *, search: Optional[str], limit: int
) -> list[tuple[int, str]]:
    """Warehouse candidates. Returns [] when the warehouse table is unavailable."""
    if not _table_exists(conn, "dim_artista"):
        return []
    term = (search or "").strip()
    if term:
        rows = conn.execute(
            """
            SELECT id_artista, nombre_artista
            FROM dim_artista
            WHERE nombre_artista IS NOT NULL
              AND LOWER(nombre_artista) LIKE LOWER(?)
            ORDER BY LENGTH(nombre_artista), id_artista
            LIMIT ?
            """,
            [f"%{term}%", limit],
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT id_artista, nombre_artista
            FROM dim_artista
            WHERE nombre_artista IS NOT NULL
            ORDER BY id_artista
            LIMIT ?
            """,
            [limit],
        ).fetchall()
    return [(int(r[0]), str(r[1])) for r in rows]


def _pending_request_for(
    conn: duckdb.DuckDBPyConnection,
    *,
    user_id: int,
    warehouse_artist_id: int,
    artist_profile_id: Optional[int],
) -> Optional[dict[str, Any]]:
    row = conn.execute(
        f"""
        SELECT {_REQUEST_SELECT}
        FROM app_artist_access_request
        WHERE applicant_user_id = ? AND status = 'pending'
          AND (warehouse_artist_id = ?
               OR (? IS NOT NULL AND target_artist_profile_id = ?))
        ORDER BY id DESC
        LIMIT 1
        """,
        [user_id, warehouse_artist_id, artist_profile_id, artist_profile_id],
    ).fetchone()
    return _request_dict(row) if row else None


def _discovery_item(
    conn: duckdb.DuckDBPyConnection,
    *,
    user_id: int,
    warehouse_artist_id: int,
    name: str,
) -> dict[str, Any]:
    """Resolve management state and the single action the caller may take."""
    profile = _find_profile_by_warehouse(conn, warehouse_artist_id)
    profile_id = profile["id"] if profile else None
    pending = _pending_request_for(
        conn,
        user_id=user_id,
        warehouse_artist_id=warehouse_artist_id,
        artist_profile_id=profile_id,
    )

    membership = (
        _active_membership(conn, artist_profile_id=profile_id, user_id=user_id)
        if profile_id is not None
        else None
    )
    owners = _count_active_owners(conn, profile_id) if profile_id is not None else 0

    if membership is not None:
        state, action = "member", "open_space"
    elif pending is not None:
        state, action = "pending", "view_request"
    elif profile_id is None or owners == 0:
        state, action = "unmanaged", "claim_ownership"
    else:
        state, action = "managed", "request_access"

    return {
        "warehouse_artist_id": warehouse_artist_id,
        "display_name": name,
        "image_url": (profile or {}).get("image_url"),
        "management_state": state,
        "allowed_action": action,
        "artist_profile_id": profile_id,
        "request_id": (pending or {}).get("id"),
        "request_status": (pending or {}).get("status"),
    }


def _invitation_row(conn: duckdb.DuckDBPyConnection, invitation_id: int) -> tuple:
    row = conn.execute(
        """
        SELECT id, artist_profile_id, email_normalized, token_hash, role, status,
               expires_at, invited_by, accepted_by, accepted_at, revoked_by, revoked_at,
               created_at, updated_at
        FROM app_artist_invitation WHERE id = ?
        """,
        [invitation_id],
    ).fetchone()
    if not row:
        raise NotFoundError(f"Invitation {invitation_id} not found")
    return row


def _invitation_public_dict(row: tuple) -> dict[str, Any]:
    """Safe invitation payload — never includes token_hash or plaintext."""
    return {
        "id": int(row[0]),
        "email_normalized": str(row[2]),
        "role": str(row[4]),
        "status": str(row[5]),
        "expires_at": row[6],
        "created_at": row[12],
        "updated_at": row[13],
    }


def _create_membership(
    conn: duckdb.DuckDBPyConnection,
    *,
    artist_profile_id: int,
    user_id: int,
    role: str,
) -> dict[str, Any]:
    if role not in ALL_ROLES:
        raise ValidationError(f"Invalid role: {role}")
    existing = _active_membership(conn, artist_profile_id=artist_profile_id, user_id=user_id)
    if existing:
        raise ConflictError("Active membership already exists for this user and artist")
    if role == "owner" and _count_active_owners(conn, artist_profile_id) > 0:
        raise ConflictError("Artist already has an active owner")
    now = _now()
    mid = _next_id(conn, "app_artist_membership")
    conn.execute(
        """
        INSERT INTO app_artist_membership
            (id, artist_profile_id, user_id, role, status, created_at, updated_at, revoked_at)
        VALUES (?, ?, ?, ?, 'active', ?, ?, NULL)
        """,
        [mid, artist_profile_id, user_id, role, now, now],
    )
    return {
        "id": mid,
        "artist_profile_id": artist_profile_id,
        "user_id": user_id,
        "role": role,
        "status": "active",
        "created_at": now,
        "updated_at": now,
        "revoked_at": None,
    }


def _revoke_membership_row(
    conn: duckdb.DuckDBPyConnection, membership_id: int
) -> None:
    """DELETE+re-INSERT pattern avoided; status mutate via delete+insert same id."""
    row = conn.execute(
        """
        SELECT id, artist_profile_id, user_id, role, status, created_at, updated_at, revoked_at
        FROM app_artist_membership WHERE id = ?
        """,
        [membership_id],
    ).fetchone()
    if not row:
        raise NotFoundError(f"Membership {membership_id} not found")
    now = _now()
    conn.execute("DELETE FROM app_artist_membership WHERE id = ?", [membership_id])
    conn.execute(
        """
        INSERT INTO app_artist_membership
            (id, artist_profile_id, user_id, role, status, created_at, updated_at, revoked_at)
        VALUES (?, ?, ?, ?, 'revoked', ?, ?, ?)
        """,
        [int(row[0]), int(row[1]), int(row[2]), str(row[3]), row[5], now, now],
    )


def _update_membership_role(
    conn: duckdb.DuckDBPyConnection, membership_id: int, new_role: str
) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT id, artist_profile_id, user_id, role, status, created_at, updated_at, revoked_at
        FROM app_artist_membership WHERE id = ?
        """,
        [membership_id],
    ).fetchone()
    if not row:
        raise NotFoundError(f"Membership {membership_id} not found")
    if str(row[4]) != "active":
        raise ValidationError("Cannot change role of revoked membership")
    now = _now()
    conn.execute("DELETE FROM app_artist_membership WHERE id = ?", [membership_id])
    conn.execute(
        """
        INSERT INTO app_artist_membership
            (id, artist_profile_id, user_id, role, status, created_at, updated_at, revoked_at)
        VALUES (?, ?, ?, ?, 'active', ?, ?, NULL)
        """,
        [int(row[0]), int(row[1]), int(row[2]), new_role, row[5], now],
    )
    return {
        "id": int(row[0]),
        "artist_profile_id": int(row[1]),
        "user_id": int(row[2]),
        "role": new_role,
        "status": "active",
        "created_at": row[5],
        "updated_at": now,
        "revoked_at": None,
    }


def _create_profile(
    conn: duckdb.DuckDBPyConnection,
    *,
    display_name: str,
    organization_id: int,
    warehouse_artist_id: Optional[int],
    created_by: int,
    legal_name: Optional[str] = None,
) -> dict[str, Any]:
    name = display_name.strip()
    if not name:
        raise ValidationError("display_name is required")
    if len(name) > 200:
        raise ValidationError("display_name must be at most 200 characters")
    now = _now()
    aid = _next_id(conn, "app_artist_profile")
    normalized = _normalize_name(name)
    conn.execute(
        f"""
        INSERT INTO app_artist_profile ({', '.join(_PROFILE_COLS)})
        VALUES ({', '.join('?' for _ in _PROFILE_COLS)})
        """,
        [
            aid,
            organization_id,
            name,
            legal_name,
            normalized,
            "active",
            warehouse_artist_id,
            created_by,
            now,
            now,
            None,
            None,
            None,
            None,
            None,
        ],
    )
    return _get_profile(conn, aid)


def _mine_item(
    conn: duckdb.DuckDBPyConnection, membership: dict[str, Any], profile: dict[str, Any]
) -> dict[str, Any]:
    return {
        "artist_profile_id": profile["id"],
        "warehouse_artist_id": profile["warehouse_artist_id"],
        "display_name": profile["display_name"],
        "image_url": profile.get("image_url"),
        "membership_role": membership["role"],
        "membership_status": membership["status"],
        "permissions": permissions_for_role(membership["role"]),
        "organization_id": profile["organization_id"]
        if profile["organization_id"] is not None
        else INDEPENDENT_ORG_ID,
    }


class ArtistSpaceUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def list_mine(self, user_id: int) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT m.id, m.artist_profile_id, m.user_id, m.role, m.status,
                   m.created_at, m.updated_at, m.revoked_at
            FROM app_artist_membership m
            WHERE m.user_id = ? AND m.status = 'active'
            ORDER BY m.id
            """,
            [user_id],
        ).fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            m = _membership_dict(row)
            try:
                profile = self._migrated_profile(m["artist_profile_id"])
            except NotFoundError:
                continue
            items.append(_mine_item(self._conn, m, profile))
        return items

    def _migrated_profile(self, artist_profile_id: int) -> dict[str, Any]:
        """Read a profile, moving legacy sentinel-backed rows onto a real workspace."""
        profile = _get_profile(self._conn, artist_profile_id)
        if profile["organization_id"] != INDEPENDENT_ORG_ID:
            return profile
        migrate_zero_backed_profile(self._conn, artist_profile_id)
        return _get_profile(self._conn, artist_profile_id)

    def summary(self, *, artist_profile_id: int, user_id: int) -> dict[str, Any]:
        m = _require_membership(
            self._conn,
            artist_profile_id=artist_profile_id,
            user_id=user_id,
            permission="artist_space.view",
        )
        profile = self._migrated_profile(artist_profile_id)
        team_size = int(
            self._conn.execute(
                """
                SELECT COUNT(*) FROM app_artist_membership
                WHERE artist_profile_id = ? AND status = 'active'
                """,
                [artist_profile_id],
            ).fetchone()[0]
        )
        pending_requests = 0
        if role_has_permission(m["role"], "artist_space.access.review"):
            pending_requests = int(
                self._conn.execute(
                    """
                    SELECT COUNT(*) FROM app_artist_access_request
                    WHERE target_artist_profile_id = ? AND status = 'pending'
                      AND request_type = 'request_access'
                    """,
                    [artist_profile_id],
                ).fetchone()[0]
            )
        track_count = 0
        wid = profile["warehouse_artist_id"]
        if wid is not None and _table_exists(self._conn, "dim_track"):
            track_count = int(
                self._conn.execute(
                    "SELECT COUNT(*) FROM dim_track WHERE id_artista = ?",
                    [wid],
                ).fetchone()[0]
            )
        return {
            "artist_profile_id": artist_profile_id,
            "display_name": profile["display_name"],
            "membership_role": m["role"],
            "team_size": team_size,
            "pending_access_requests": pending_requests,
            "track_count": track_count,
            "organization_id": profile["organization_id"],
            "warehouse_artist_id": wid,
        }

    def get_profile(self, *, artist_profile_id: int, user_id: int) -> dict[str, Any]:
        m = _require_membership(
            self._conn,
            artist_profile_id=artist_profile_id,
            user_id=user_id,
            permission="artist_space.view",
        )
        profile = _get_profile(self._conn, artist_profile_id)
        if not role_has_permission(m["role"], "artist_space.profile.update"):
            # legal_name is non-public: owner/administrator only.
            profile = {**profile, "legal_name": None}
        return {
            **profile,
            "membership_role": m["role"],
            "permissions": permissions_for_role(m["role"]),
            "external_identifiers": _list_external_identifiers(
                self._conn, artist_profile_id
            ),
        }

    def patch_profile(
        self,
        *,
        artist_profile_id: int,
        user_id: int,
        display_name: Optional[str] = None,
        legal_name: Optional[str] = None,
        bio: Optional[str] = None,
        country_code: Optional[str] = None,
        primary_genre: Optional[str] = None,
        website_url: Optional[str] = None,
        image_url: Optional[str] = None,
        external_identifiers: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        _require_membership(
            self._conn,
            artist_profile_id=artist_profile_id,
            user_id=user_id,
            permission="artist_space.profile.update",
        )
        _get_profile(self._conn, artist_profile_id)
        changes: dict[str, Any] = {"updated_at": _now()}
        if display_name is not None:
            name = display_name.strip()
            if not name:
                raise ValidationError("display_name cannot be empty")
            if len(name) > 200:
                raise ValidationError("display_name must be at most 200 characters")
            changes["display_name"] = name
            changes["normalized_name"] = _normalize_name(name)
        if legal_name is not None:
            changes["legal_name"] = legal_name.strip() or None
        if bio is not None:
            text = bio.strip()
            if len(text) > 2000:
                raise ValidationError("bio must be at most 2000 characters")
            changes["bio"] = text or None
        if country_code is not None:
            code = country_code.strip().upper()
            if code and not re.fullmatch(r"[A-Z]{2}", code):
                raise ValidationError("country_code must be a 2-letter ISO code")
            changes["country_code"] = code or None
        if primary_genre is not None:
            genre = primary_genre.strip()
            if len(genre) > 80:
                raise ValidationError("primary_genre must be at most 80 characters")
            changes["primary_genre"] = genre or None
        if website_url is not None:
            url = website_url.strip()
            changes["website_url"] = (
                _validate_http_url(url, field="website_url") if url else None
            )
        if image_url is not None:
            url = image_url.strip()
            changes["image_url"] = (
                _validate_http_url(url, field="image_url") if url else None
            )

        # Both writes validate up front, then run in autocommit: DuckDB rejects
        # rewriting a pre-existing indexed row inside an explicit transaction.
        identifiers = (
            _normalize_external_identifiers(external_identifiers)
            if external_identifiers is not None
            else None
        )
        # DuckDB-safe profile mutate (same pattern as Spec 020)
        _update_profile_row(self._conn, artist_profile_id, **changes)
        if identifiers is not None:
            _replace_external_identifiers(self._conn, artist_profile_id, identifiers)
        return self.get_profile(artist_profile_id=artist_profile_id, user_id=user_id)

    def list_tracks(
        self, *, artist_profile_id: int, user_id: int, limit: int = 50, offset: int = 0
    ) -> dict[str, Any]:
        _require_membership(
            self._conn,
            artist_profile_id=artist_profile_id,
            user_id=user_id,
            permission="artist_space.view",
        )
        profile = _get_profile(self._conn, artist_profile_id)
        wid = profile["warehouse_artist_id"]
        if wid is None:
            return {"items": [], "total": 0, "empty_reason": "no_warehouse_link"}
        try:
            total = int(
                self._conn.execute(
                    "SELECT COUNT(*) FROM dim_track WHERE id_artista = ?",
                    [wid],
                ).fetchone()[0]
            )
            rows = self._conn.execute(
                """
                SELECT id_track, nombre_track, id_artista, duration_ms
                FROM dim_track WHERE id_artista = ?
                ORDER BY id_track
                LIMIT ? OFFSET ?
                """,
                [wid, limit, offset],
            ).fetchall()
        except Exception:
            return {"items": [], "total": 0, "empty_reason": "catalog_unavailable"}
        items = [
            {
                "id_track": int(r[0]),
                "nombre_track": str(r[1]),
                "id_artista": int(r[2]) if r[2] is not None else None,
                "duration_ms": int(r[3]) if r[3] is not None else None,
            }
            for r in rows
        ]
        return {"items": items, "total": total}

    def list_releases(
        self, *, artist_profile_id: int, user_id: int, limit: int = 50, offset: int = 0
    ) -> dict[str, Any]:
        _require_membership(
            self._conn,
            artist_profile_id=artist_profile_id,
            user_id=user_id,
            permission="artist_space.view",
        )
        try:
            total = int(
                self._conn.execute(
                    """
                    SELECT COUNT(*) FROM app_release_submission
                    WHERE artist_profile_id = ?
                    """,
                    [artist_profile_id],
                ).fetchone()[0]
            )
            rows = self._conn.execute(
                """
                SELECT id, title, status, release_type, created_at
                FROM app_release_submission
                WHERE artist_profile_id = ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                [artist_profile_id, limit, offset],
            ).fetchall()
        except Exception:
            return {"items": [], "total": 0, "empty_reason": "no_publishing_releases"}
        items = [
            {
                "id": int(r[0]),
                "title": str(r[1]),
                "status": str(r[2]) if r[2] is not None else None,
                "release_type": str(r[3]) if r[3] is not None else None,
                "created_at": r[4],
            }
            for r in rows
        ]
        return {"items": items, "total": total}

    def list_team(self, *, artist_profile_id: int, user_id: int) -> list[dict[str, Any]]:
        _require_membership(
            self._conn,
            artist_profile_id=artist_profile_id,
            user_id=user_id,
            permission="artist_space.view",
        )
        rows = self._conn.execute(
            """
            SELECT id, artist_profile_id, user_id, role, status, created_at, updated_at, revoked_at
            FROM app_artist_membership
            WHERE artist_profile_id = ? AND status = 'active'
            ORDER BY CASE role
                WHEN 'owner' THEN 0
                WHEN 'administrator' THEN 1
                WHEN 'member' THEN 2
                ELSE 3 END, id
            """,
            [artist_profile_id],
        ).fetchall()
        out = []
        for row in rows:
            m = _membership_dict(row)
            user = _fetch_user(self._conn, m["user_id"])
            m["email"] = (user or {}).get("email")
            m["display_name"] = (user or {}).get("display_name") or (user or {}).get("username")
            m["permissions"] = permissions_for_role(m["role"])
            out.append(m)
        return out

    def create_invitation(
        self,
        *,
        artist_profile_id: int,
        user_id: int,
        email: str,
        role: str,
        ttl_days: int = DEFAULT_INVITE_TTL_DAYS,
    ) -> dict[str, Any]:
        _require_membership(
            self._conn,
            artist_profile_id=artist_profile_id,
            user_id=user_id,
            permission="artist_space.invite",
        )
        role_n = (role or "").strip().lower()
        if role_n not in INVITE_ROLES:
            raise ValidationError("Invitation role must be administrator, member, or reader")
        email_n = normalize_email(email)
        if not email_n:
            raise ValidationError("email is required")
        if ttl_days < 1 or ttl_days > 30:
            raise ValidationError("ttl_days must be between 1 and 30")

        existing_user = self._conn.execute(
            "SELECT id FROM app_user WHERE LOWER(email) = ?", [email_n]
        ).fetchone()
        if existing_user:
            if _active_membership(
                self._conn,
                artist_profile_id=artist_profile_id,
                user_id=int(existing_user[0]),
            ):
                raise ConflictError("User is already an active member")

        pending = self._conn.execute(
            """
            SELECT id FROM app_artist_invitation
            WHERE artist_profile_id = ? AND email_normalized = ? AND status = 'pending'
            LIMIT 1
            """,
            [artist_profile_id, email_n],
        ).fetchone()
        if pending:
            raise ConflictError("Pending invitation already exists for this email")

        token = generate_invitation_token()
        now = _now()
        expires = now + timedelta(days=ttl_days)
        iid = _next_id(self._conn, "app_artist_invitation")
        self._conn.execute(
            """
            INSERT INTO app_artist_invitation
                (id, artist_profile_id, email_normalized, token_hash, role, status,
                 expires_at, invited_by, accepted_by, accepted_at, revoked_by, revoked_at,
                 created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, NULL, NULL, NULL, NULL, ?, ?)
            """,
            [
                iid,
                artist_profile_id,
                email_n,
                token.token_hash,
                role_n,
                expires,
                user_id,
                now,
                now,
            ],
        )
        return {
            "invitation_id": iid,
            "artist_profile_id": artist_profile_id,
            "email_normalized": email_n,
            "role": role_n,
            "status": "pending",
            "expires_at": expires,
            "invite_token": token.plaintext,
            "returned_once": True,
            "email_delivery_status": token.email_delivery_status,
        }

    def list_invitations(
        self,
        *,
        artist_profile_id: int,
        user_id: int,
        status: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        _require_membership(
            self._conn,
            artist_profile_id=artist_profile_id,
            user_id=user_id,
            permission="artist_space.invite",
        )
        sql = """
            SELECT id, artist_profile_id, email_normalized, token_hash, role, status,
                   expires_at, invited_by, accepted_by, accepted_at, revoked_by, revoked_at,
                   created_at, updated_at
            FROM app_artist_invitation
            WHERE artist_profile_id = ?
        """
        params: list[Any] = [artist_profile_id]
        if status:
            status_n = status.strip().lower()
            sql += " AND status = ?"
            params.append(status_n)
        sql += " ORDER BY id DESC"
        rows = self._conn.execute(sql, params).fetchall()
        return [_invitation_public_dict(r) for r in rows]

    def revoke_invitation(
        self, *, artist_profile_id: int, user_id: int, invitation_id: int
    ) -> dict[str, Any]:
        _require_membership(
            self._conn,
            artist_profile_id=artist_profile_id,
            user_id=user_id,
            permission="artist_space.invite",
        )
        row = _invitation_row(self._conn, invitation_id)
        if int(row[1]) != artist_profile_id:
            raise NotFoundError("Invitation not found on this artist")
        status = str(row[5])
        if status == "accepted":
            raise ValidationError(
                "Accepted invitation cannot be revoked; use team revoke to remove membership"
            )
        if status == "revoked":
            raise ValidationError("Invitation already revoked")
        if status != "pending":
            raise ValidationError(f"Only pending invitations can be revoked (status={status})")
        now = _now()
        self._conn.execute("DELETE FROM app_artist_invitation WHERE id = ?", [invitation_id])
        self._conn.execute(
            """
            INSERT INTO app_artist_invitation
                (id, artist_profile_id, email_normalized, token_hash, role, status,
                 expires_at, invited_by, accepted_by, accepted_at, revoked_by, revoked_at,
                 created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'revoked', ?, ?, NULL, NULL, ?, ?, ?, ?)
            """,
            [
                int(row[0]),
                int(row[1]),
                str(row[2]),
                str(row[3]),
                str(row[4]),
                row[6],
                int(row[7]) if row[7] is not None else None,
                user_id,
                now,
                row[12],
                now,
            ],
        )
        return _invitation_public_dict(_invitation_row(self._conn, invitation_id))

    def resend_invitation(
        self,
        *,
        artist_profile_id: int,
        user_id: int,
        invitation_id: int,
        ttl_days: int = DEFAULT_INVITE_TTL_DAYS,
    ) -> dict[str, Any]:
        _require_membership(
            self._conn,
            artist_profile_id=artist_profile_id,
            user_id=user_id,
            permission="artist_space.invite",
        )
        if ttl_days < 1 or ttl_days > 30:
            raise ValidationError("ttl_days must be between 1 and 30")
        row = _invitation_row(self._conn, invitation_id)
        if int(row[1]) != artist_profile_id:
            raise NotFoundError("Invitation not found on this artist")
        if str(row[5]) != "pending":
            raise ValidationError("Only pending invitations can be resent")
        token = generate_invitation_token()
        now = _now()
        expires = now + timedelta(days=ttl_days)
        self._conn.execute("DELETE FROM app_artist_invitation WHERE id = ?", [invitation_id])
        self._conn.execute(
            """
            INSERT INTO app_artist_invitation
                (id, artist_profile_id, email_normalized, token_hash, role, status,
                 expires_at, invited_by, accepted_by, accepted_at, revoked_by, revoked_at,
                 created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, NULL, NULL, NULL, NULL, ?, ?)
            """,
            [
                int(row[0]),
                int(row[1]),
                str(row[2]),
                token.token_hash,
                str(row[4]),
                expires,
                int(row[7]) if row[7] is not None else None,
                row[12],
                now,
            ],
        )
        return {
            "invitation_id": int(row[0]),
            "artist_profile_id": artist_profile_id,
            "email_normalized": str(row[2]),
            "role": str(row[4]),
            "status": "pending",
            "expires_at": expires,
            "invite_token": token.plaintext,
            "returned_once": True,
            "email_delivery_status": token.email_delivery_status,
        }

    def revoke_member(
        self, *, artist_profile_id: int, user_id: int, membership_id: int
    ) -> dict[str, Any]:
        _require_membership(
            self._conn,
            artist_profile_id=artist_profile_id,
            user_id=user_id,
            permission="artist_space.team.manage",
        )
        row = self._conn.execute(
            """
            SELECT id, artist_profile_id, user_id, role, status
            FROM app_artist_membership WHERE id = ?
            """,
            [membership_id],
        ).fetchone()
        if not row or int(row[1]) != artist_profile_id:
            raise NotFoundError("Membership not found on this artist")
        if str(row[4]) != "active":
            raise ValidationError("Membership already revoked")
        if str(row[3]) == "owner" and _count_active_owners(self._conn, artist_profile_id) <= 1:
            raise ValidationError("Cannot revoke the last active owner")
        _revoke_membership_row(self._conn, membership_id)
        return {"id": membership_id, "status": "revoked"}

    def change_role(
        self,
        *,
        artist_profile_id: int,
        user_id: int,
        membership_id: int,
        new_role: str,
    ) -> dict[str, Any]:
        _require_membership(
            self._conn,
            artist_profile_id=artist_profile_id,
            user_id=user_id,
            permission="artist_space.team.manage",
        )
        role_n = (new_role or "").strip().lower()
        if role_n == "owner":
            raise ValidationError("Cannot promote to owner via role change")
        if role_n not in INVITE_ROLES:
            raise ValidationError("Invalid role")
        row = self._conn.execute(
            """
            SELECT id, artist_profile_id, user_id, role, status
            FROM app_artist_membership WHERE id = ?
            """,
            [membership_id],
        ).fetchone()
        if not row or int(row[1]) != artist_profile_id:
            raise NotFoundError("Membership not found on this artist")
        if str(row[4]) != "active":
            raise ValidationError("Membership is not active")
        if str(row[3]) == "owner" and _count_active_owners(self._conn, artist_profile_id) <= 1:
            raise ValidationError("Cannot change role of the last active owner")
        return _update_membership_role(self._conn, membership_id, role_n)

    def accept_invitation(self, *, user_id: int, raw_token: str) -> dict[str, Any]:
        token = (raw_token or "").strip()
        if not token:
            raise ValidationError("token is required")
        th = hash_invitation_token(token)
        row = self._conn.execute(
            """
            SELECT id, artist_profile_id, email_normalized, token_hash, role, status,
                   expires_at, invited_by, accepted_by, accepted_at, revoked_by, revoked_at,
                   created_at, updated_at
            FROM app_artist_invitation WHERE token_hash = ?
            """,
            [th],
        ).fetchone()
        if not row:
            raise NotFoundError("Invitation not found")
        status = str(row[5])
        if status == "accepted":
            raise InvitationAlreadyUsed("Invitation already accepted")
        if status == "revoked":
            raise InvitationRevoked("Invitation revoked")
        if status == "expired":
            raise InvitationExpired("Invitation expired")
        expires_at = row[6]
        now = _now()
        if expires_at is not None and expires_at < now:
            # mark expired
            self._conn.execute(
                """
                DELETE FROM app_artist_invitation WHERE id = ?
                """,
                [int(row[0])],
            )
            self._conn.execute(
                """
                INSERT INTO app_artist_invitation
                    (id, artist_profile_id, email_normalized, token_hash, role, status,
                     expires_at, invited_by, accepted_by, accepted_at, revoked_by, revoked_at,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'expired', ?, ?, NULL, NULL, NULL, NULL, ?, ?)
                """,
                [
                    int(row[0]),
                    int(row[1]),
                    str(row[2]),
                    str(row[3]),
                    str(row[4]),
                    expires_at,
                    int(row[7]),
                    row[12],
                    now,
                ],
            )
            raise InvitationExpired("Invitation expired")

        user = _fetch_user(self._conn, user_id)
        if not user:
            raise PermissionDenied("User not found")
        user_email = normalize_email(user.get("email") or "")
        if user_email != str(row[2]):
            raise PermissionDenied("Invitation email does not match authenticated user")

        membership = _create_membership(
            self._conn,
            artist_profile_id=int(row[1]),
            user_id=user_id,
            role=str(row[4]),
        )
        # mark accepted (delete+insert)
        self._conn.execute("DELETE FROM app_artist_invitation WHERE id = ?", [int(row[0])])
        self._conn.execute(
            """
            INSERT INTO app_artist_invitation
                (id, artist_profile_id, email_normalized, token_hash, role, status,
                 expires_at, invited_by, accepted_by, accepted_at, revoked_by, revoked_at,
                 created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'accepted', ?, ?, ?, ?, NULL, NULL, ?, ?)
            """,
            [
                int(row[0]),
                int(row[1]),
                str(row[2]),
                str(row[3]),
                str(row[4]),
                expires_at,
                int(row[7]),
                user_id,
                now,
                row[12],
                now,
            ],
        )
        return {
            "membership": membership,
            "artist_profile_id": int(row[1]),
            "role": str(row[4]),
        }

    def list_pending_access_requests(
        self, *, artist_profile_id: int, user_id: int
    ) -> list[dict[str, Any]]:
        _require_membership(
            self._conn,
            artist_profile_id=artist_profile_id,
            user_id=user_id,
            permission="artist_space.access.review",
        )
        rows = self._conn.execute(
            f"""
            SELECT {_REQUEST_SELECT}
            FROM app_artist_access_request
            WHERE target_artist_profile_id = ? AND status = 'pending'
              AND request_type = 'request_access'
            ORDER BY id
            """,
            [artist_profile_id],
        ).fetchall()
        return [_request_dict(r) for r in rows]

    def approve_access_request(
        self, *, artist_profile_id: int, user_id: int, request_id: int
    ) -> dict[str, Any]:
        _require_membership(
            self._conn,
            artist_profile_id=artist_profile_id,
            user_id=user_id,
            permission="artist_space.access.review",
        )
        req = _get_request(self._conn, request_id)
        if req["status"] != "pending":
            raise ValidationError("Request is not pending")
        if req["request_type"] != "request_access":
            raise ValidationError("Only request_access can be approved by artist owners")
        if req["target_artist_profile_id"] != artist_profile_id:
            raise PermissionDenied("Request does not target this artist")
        role = (req["proposed_role"] or "member").strip().lower()
        if role == "owner" or role not in INVITE_ROLES:
            role = "member"
        membership = _create_membership(
            self._conn,
            artist_profile_id=artist_profile_id,
            user_id=req["applicant_user_id"],
            role=role,
        )
        _set_request_status(
            self._conn, request_id, status="approved", reviewer_user_id=user_id
        )
        return {"request_id": request_id, "membership": membership}

    def reject_access_request(
        self,
        *,
        artist_profile_id: int,
        user_id: int,
        request_id: int,
        reason: Optional[str] = None,
    ) -> dict[str, Any]:
        _require_membership(
            self._conn,
            artist_profile_id=artist_profile_id,
            user_id=user_id,
            permission="artist_space.access.review",
        )
        req = _get_request(self._conn, request_id)
        if req["status"] != "pending":
            raise ValidationError("Request is not pending")
        if req["target_artist_profile_id"] != artist_profile_id:
            raise PermissionDenied("Request does not target this artist")
        _set_request_status(
            self._conn,
            request_id,
            status="rejected",
            reviewer_user_id=user_id,
            rejection_reason=reason,
        )
        return {"request_id": request_id, "status": "rejected"}


def _request_dict(row: tuple) -> dict[str, Any]:
    data = dict(zip(_REQUEST_COLS, row))
    return {
        **data,
        "id": int(data["id"]),
        "applicant_user_id": int(data["applicant_user_id"]),
        "request_type": str(data["request_type"]),
        "target_artist_profile_id": (
            int(data["target_artist_profile_id"])
            if data["target_artist_profile_id"] is not None
            else None
        ),
        "warehouse_artist_id": (
            int(data["warehouse_artist_id"])
            if data["warehouse_artist_id"] is not None
            else None
        ),
        "proposed_role": data["proposed_role"] or "member",
        "status": str(data["status"]),
        "reviewer_user_id": (
            int(data["reviewer_user_id"]) if data["reviewer_user_id"] is not None else None
        ),
    }


def _get_request(conn: duckdb.DuckDBPyConnection, request_id: int) -> dict[str, Any]:
    row = conn.execute(
        f"SELECT {_REQUEST_SELECT} FROM app_artist_access_request WHERE id = ?",
        [request_id],
    ).fetchone()
    if not row:
        raise NotFoundError(f"Access request {request_id} not found")
    return _request_dict(row)


def _set_request_status(
    conn: duckdb.DuckDBPyConnection,
    request_id: int,
    *,
    status: str,
    reviewer_user_id: Optional[int] = None,
    rejection_reason: Optional[str] = None,
) -> None:
    """Record a review decision, preserving the request id.

    Same DuckDB constraint as ``_update_profile_row``: must run in autocommit,
    never inside an open ``transactional()`` block.
    """
    req = _get_request(conn, request_id)
    req.update(
        {
            "status": status,
            "reviewed_at": _now(),
            "reviewer_user_id": reviewer_user_id,
            "rejection_reason": rejection_reason,
        }
    )
    conn.execute("DELETE FROM app_artist_access_request WHERE id = ?", [request_id])
    conn.execute(
        f"""
        INSERT INTO app_artist_access_request ({_REQUEST_SELECT})
        VALUES ({', '.join('?' for _ in _REQUEST_COLS)})
        """,
        [req[c] for c in _REQUEST_COLS],
    )


class ArtistAccessRequestUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        user_id: int,
        request_type: str,
        warehouse_artist_id: Optional[int] = None,
        target_artist_profile_id: Optional[int] = None,
        proposed_display_name: Optional[str] = None,
        proposed_role: Optional[str] = None,
        relationship_type: Optional[str] = None,
        evidence_url: Optional[str] = None,
        evidence_note: Optional[str] = None,
        accuracy_attested: bool = False,
    ) -> dict[str, Any]:
        rt = (request_type or "").strip().lower()
        if rt not in REQUEST_TYPES:
            raise ValidationError(f"Invalid request_type: {request_type}")

        relationship = (relationship_type or "").strip().lower() or None
        evidence_url = (evidence_url or "").strip() or None
        evidence_note = (evidence_note or "").strip() or None
        if relationship is not None and relationship not in RELATIONSHIP_TYPES:
            raise ValidationError(
                "relationship_type must be one of: "
                + ", ".join(sorted(RELATIONSHIP_TYPES))
            )
        if evidence_url is not None:
            _validate_http_url(evidence_url, field="evidence_url")

        if rt == "claim_ownership":
            if relationship is None:
                raise EvidenceRequired("relationship_type is required for claim_ownership")
            if evidence_url is None and evidence_note is None:
                raise EvidenceRequired(
                    "evidence_url or evidence_note is required for claim_ownership"
                )
            if warehouse_artist_id is None:
                raise ValidationError("warehouse_artist_id is required for claim_ownership")
            if not _warehouse_exists(self._conn, warehouse_artist_id):
                raise NotFoundError("Warehouse artist not found")
            profile = _find_profile_by_warehouse(self._conn, warehouse_artist_id)
            if profile and _count_active_owners(self._conn, profile["id"]) > 0:
                raise ConflictError("Artist profile already has an active owner")
            target_artist_profile_id = profile["id"] if profile else None

        elif rt == "request_access":
            profile = None
            if target_artist_profile_id is not None:
                profile = _get_profile(self._conn, target_artist_profile_id)
            elif warehouse_artist_id is not None:
                profile = _find_profile_by_warehouse(self._conn, warehouse_artist_id)
                if profile is None:
                    raise NotFoundError(
                        "No management profile linked to this warehouse artist; claim ownership instead"
                    )
                target_artist_profile_id = profile["id"]
            else:
                raise ValidationError(
                    "target_artist_profile_id or warehouse_artist_id is required for request_access"
                )
            if _count_active_owners(self._conn, profile["id"]) < 1:
                raise ValidationError("Artist has no owner; use claim_ownership instead")
            if _active_membership(
                self._conn, artist_profile_id=profile["id"], user_id=user_id
            ):
                raise ConflictError("Already an active member")
            role = (proposed_role or "member").strip().lower()
            if role == "owner" or role not in INVITE_ROLES:
                raise ValidationError("proposed_role must be administrator, member, or reader")
            proposed_role = role

        elif rt == "create_new":
            name = (proposed_display_name or "").strip()
            if not name:
                raise ValidationError("proposed_display_name is required for create_new")
            if relationship is None:
                raise EvidenceRequired("relationship_type is required for create_new")
            if not accuracy_attested:
                raise EvidenceRequired(
                    "accuracy_attested must be true to request a new artist"
                )
            proposed_display_name = name

        # pending duplicate check (same applicant + type + target)
        dup = self._conn.execute(
            """
            SELECT id FROM app_artist_access_request
            WHERE applicant_user_id = ? AND request_type = ? AND status = 'pending'
              AND (
                (? IS NOT NULL AND warehouse_artist_id = ?)
                OR (? IS NOT NULL AND target_artist_profile_id = ?)
                OR (? IS NOT NULL AND proposed_display_name = ?)
              )
            LIMIT 1
            """,
            [
                user_id,
                rt,
                warehouse_artist_id,
                warehouse_artist_id,
                target_artist_profile_id,
                target_artist_profile_id,
                proposed_display_name,
                proposed_display_name,
            ],
        ).fetchone()
        if dup:
            raise ConflictError("Pending request already exists")

        now = _now()
        rid = _next_id(self._conn, "app_artist_access_request")
        self._conn.execute(
            f"""
            INSERT INTO app_artist_access_request ({_REQUEST_SELECT})
            VALUES ({', '.join('?' for _ in _REQUEST_COLS)})
            """,
            [
                rid,
                user_id,
                rt,
                target_artist_profile_id,
                warehouse_artist_id,
                proposed_display_name,
                proposed_role or "member",
                "pending",
                now,
                None,
                None,
                None,
                relationship,
                evidence_url,
                evidence_note,
            ],
        )
        return _get_request(self._conn, rid)

    def discover(
        self,
        *,
        user_id: int,
        search: Optional[str] = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Warehouse artist candidates enriched with a single server-chosen action."""
        limit = max(1, min(int(limit), 100))
        rows = _search_warehouse_artists(self._conn, search=search, limit=limit)
        items = [
            _discovery_item(self._conn, user_id=user_id, warehouse_artist_id=wid, name=name)
            for wid, name in rows
        ]
        return {"items": items, "total": len(items)}

    def list_mine(self, user_id: int) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            f"""
            SELECT {_REQUEST_SELECT}
            FROM app_artist_access_request
            WHERE applicant_user_id = ?
            ORDER BY id DESC
            """,
            [user_id],
        ).fetchall()
        return [_request_dict(r) for r in rows]

    def cancel(self, *, user_id: int, request_id: int) -> dict[str, Any]:
        req = _get_request(self._conn, request_id)
        if req["applicant_user_id"] != user_id:
            raise PermissionDenied("Can only cancel own requests")
        if req["status"] != "pending":
            raise ValidationError("Only pending requests can be cancelled")
        _set_request_status(self._conn, request_id, status="cancelled", reviewer_user_id=user_id)
        return {"id": request_id, "status": "cancelled"}


class PlatformArtistRequestUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def _require_admin(self, user_id: int) -> None:
        if not is_platform_admin(self._conn, user_id):
            raise PermissionDenied("Platform admin required")

    def list(
        self, *, user_id: int, status: Optional[str] = "pending"
    ) -> list[dict[str, Any]]:
        self._require_admin(user_id)
        sql = f"""
            SELECT {_REQUEST_SELECT}
            FROM app_artist_access_request
            WHERE request_type IN ('claim_ownership', 'create_new')
        """
        params: list[Any] = []
        if status:
            sql += " AND status = ?"
            params.append(status)
        sql += " ORDER BY id"
        rows = self._conn.execute(sql, params).fetchall()
        return [_request_dict(r) for r in rows]

    def get(self, *, user_id: int, request_id: int) -> dict[str, Any]:
        self._require_admin(user_id)
        req = _get_request(self._conn, request_id)
        if req["request_type"] not in ("claim_ownership", "create_new"):
            raise NotFoundError("Not a platform-reviewable request")
        return req

    def approve(self, *, user_id: int, request_id: int) -> dict[str, Any]:
        self._require_admin(user_id)
        req = _get_request(self._conn, request_id)
        if req["status"] != "pending":
            raise ValidationError("Request is not pending")
        if req["request_type"] not in ("claim_ownership", "create_new"):
            raise ValidationError("Not a platform-reviewable request")

        applicant = req["applicant_user_id"]
        # DuckDB cannot rewrite pre-existing indexed rows inside an explicit
        # transaction, so the approval is ordered instead of wrapped: the
        # workspace comes first, then profile and membership, and only then the
        # request decision. Progress is tracked as each stage commits so a
        # mid-flight failure can compensate exactly what THIS call created.
        progress = _ApprovalProgress()
        try:
            profile, membership = self._apply_approval(
                req,
                request_id=request_id,
                applicant=applicant,
                progress=progress,
            )
            progress.status_mutated = True
            _set_request_status(
                self._conn,
                request_id,
                status="approved",
                reviewer_user_id=user_id,
            )
        except Exception:
            self._undo_approval(pending_request=req, progress=progress)
            raise
        # Platform admin does NOT become a member
        return {
            "request_id": request_id,
            "status": "approved",
            "profile": profile,
            "membership": membership,
            "reviewer_became_member": False,
        }

    def _apply_approval(
        self,
        req: dict[str, Any],
        *,
        request_id: int,
        applicant: int,
        progress: "_ApprovalProgress",
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Provision the tenant, materialize the profile and grant ownership.

        Updates ``progress`` as each resource is created so the caller can
        compensate on failure even when this method raises mid-way.
        """
        if req["request_type"] == "claim_ownership":
            wid = req["warehouse_artist_id"]
            if wid is None or not _warehouse_exists(self._conn, wid):
                raise NotFoundError("Warehouse artist not found")
            profile = _find_profile_by_warehouse(self._conn, wid)
            if profile is None:
                display_name = _warehouse_name(self._conn, wid) or f"Artist {wid}"
                progress.workspace = self._provision_workspace(
                    display_name=display_name,
                    owner_user_id=applicant,
                    seed_key=f"warehouse:{wid}",
                )
                profile = _create_profile(
                    self._conn,
                    display_name=display_name,
                    organization_id=progress.workspace.organization_id,
                    warehouse_artist_id=wid,
                    created_by=applicant,
                )
                progress.created_profile_id = int(profile["id"])
            elif _count_active_owners(self._conn, profile["id"]) > 0:
                raise ConflictError("Artist already has an active owner")
            else:
                changes: dict[str, Any] = {"updated_at": _now()}
                if profile["warehouse_artist_id"] is None:
                    changes["warehouse_artist_id"] = wid
                if profile["organization_id"] == INDEPENDENT_ORG_ID:
                    progress.workspace = self._provision_workspace(
                        display_name=profile["display_name"],
                        owner_user_id=applicant,
                        seed_key=f"profile:{profile['id']}",
                    )
                    changes["organization_id"] = progress.workspace.organization_id
                if len(changes) > 1:
                    # Preexisting profile — snapshot full logical row before mutate.
                    progress.mutated_profile = dict(profile)
                    _update_profile_row(self._conn, profile["id"], **changes)
                    profile = _get_profile(self._conn, profile["id"])

        elif req["request_type"] == "create_new":
            display_name = req["proposed_display_name"] or "New Artist"
            progress.workspace = self._provision_workspace(
                display_name=display_name,
                owner_user_id=applicant,
                seed_key=f"request:{request_id}",
            )
            profile = _create_profile(
                self._conn,
                display_name=display_name,
                organization_id=progress.workspace.organization_id,
                warehouse_artist_id=None,
                created_by=applicant,
            )
            progress.created_profile_id = int(profile["id"])
        else:
            raise ValidationError("Not a platform-reviewable request")

        membership = _create_membership(
            self._conn,
            artist_profile_id=profile["id"],
            user_id=applicant,
            role="owner",
        )
        progress.membership_id = int(membership["id"])
        return profile, membership

    def _undo_approval(
        self,
        *,
        pending_request: dict[str, Any],
        progress: "_ApprovalProgress",
    ) -> None:
        """Compensate a partially applied approval so the request stays retryable.

        Deletes only resources this approval call created. Restores preexisting
        profiles / org memberships / owner roles from snapshots. Never deletes a
        reused workspace or a preexisting profile/membership/role row.
        """
        if progress.membership_id is not None:
            self._conn.execute(
                "DELETE FROM app_artist_membership WHERE id = ?",
                [progress.membership_id],
            )
        if progress.mutated_profile is not None:
            snap = progress.mutated_profile
            profile_id = int(snap["id"])
            restore = {
                k: snap[k]
                for k in (
                    "organization_id",
                    "warehouse_artist_id",
                    "updated_at",
                    "display_name",
                    "legal_name",
                    "normalized_name",
                    "status",
                    "bio",
                    "country_code",
                    "primary_genre",
                    "website_url",
                    "image_url",
                )
                if k in snap
            }
            _update_profile_row(self._conn, profile_id, **restore)
        elif progress.created_profile_id is not None:
            self._conn.execute(
                "DELETE FROM app_artist_profile WHERE id = ?",
                [progress.created_profile_id],
            )
        if progress.workspace is not None:
            ws = progress.workspace
            compensate_created_workspace(
                self._conn,
                organization_id=ws.organization_id,
                created_organization=ws.created_organization,
                created_membership_id=ws.created_membership_id,
                created_role_assignment=ws.created_role_assignment,
                created_member_role_id=ws.created_member_role_id,
                mutated_membership=ws.mutated_membership,
                mutated_member_role=ws.mutated_member_role,
            )
        if progress.status_mutated:
            self._restore_pending_request(pending_request)

    def _restore_pending_request(self, pending_request: dict[str, Any]) -> None:
        """Ensure the access request is pending again after a failed status write."""
        request_id = int(pending_request["id"])
        row = self._conn.execute(
            "SELECT status FROM app_artist_access_request WHERE id = ?",
            [request_id],
        ).fetchone()
        if row is not None and str(row[0]) == "pending":
            return
        restored = dict(pending_request)
        restored["status"] = "pending"
        restored["reviewed_at"] = None
        restored["reviewer_user_id"] = None
        restored["rejection_reason"] = None
        if row is not None:
            self._conn.execute(
                "DELETE FROM app_artist_access_request WHERE id = ?", [request_id]
            )
        self._conn.execute(
            f"""
            INSERT INTO app_artist_access_request ({_REQUEST_SELECT})
            VALUES ({', '.join('?' for _ in _REQUEST_COLS)})
            """,
            [restored[c] for c in _REQUEST_COLS],
        )

    def _provision_workspace(
        self, *, display_name: str, owner_user_id: int, seed_key: str
    ) -> WorkspaceProvisionResult:
        """Provision the hidden tenant before anything else is written.

        Any failure surfaces as ``artist_workspace_provision_failed``. On create
        failures the provisioner compensates itself; on success the rich result
        lets approve compensate later stages without deleting reused tenants.
        """
        try:
            return provision_artist_workspace(
                self._conn,
                display_name=display_name,
                owner_user_id=owner_user_id,
                seed_key=seed_key,
            )
        except WorkspaceProvisionError:
            raise
        except Exception as exc:
            raise WorkspaceProvisionError(
                f"Could not provision the artist workspace: {exc}"
            ) from exc

    def reject(
        self, *, user_id: int, request_id: int, reason: Optional[str] = None
    ) -> dict[str, Any]:
        self._require_admin(user_id)
        req = _get_request(self._conn, request_id)
        if req["status"] != "pending":
            raise ValidationError("Request is not pending")
        if req["request_type"] not in ("claim_ownership", "create_new"):
            raise ValidationError("Not a platform-reviewable request")
        _set_request_status(
            self._conn,
            request_id,
            status="rejected",
            reviewer_user_id=user_id,
            rejection_reason=reason,
        )
        return {"request_id": request_id, "status": "rejected"}


@dataclass
class _ApprovalProgress:
    """Mutable create/mutate tracking for Spec 051 approval compensation."""

    workspace: Optional[WorkspaceProvisionResult] = None
    created_profile_id: Optional[int] = None
    mutated_profile: Optional[dict[str, Any]] = None
    membership_id: Optional[int] = None
    status_mutated: bool = False