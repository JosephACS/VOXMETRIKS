"""Catalog rights consolidated use cases — Spec 021.

Covers: catalog assets/releases (business records, org-scoped, optionally
        linked to warehouse dim_track/dim_album and to app_artist_profile),
        asset ownership, rights contracts (master/publishing/neighboring/
        other), contract parties with ownership percentages, territories,
        authorized uses, approval workflow, and rights-conflict detection.

PERCENTAGE / OVERLAP RULE (see business-rules.md):
Ownership percentages are never summed globally per asset. They are only
validated for the tuple (asset_id, rights_type, territory, overlapping
applicable period). A territory with no explicit app_rights_territory row
is treated as global scope ('WORLD'), which is considered to overlap with
every other explicit territory code for the same asset/rights_type. When
the concurrent sum for any tuple exceeds 100%, a rights conflict is opened
and the contracts involved are marked 'disputed'.

app_rights_contract is a *legal-rights* record, always kept distinct from
app_commercial_contract (Spec 017 CRM/commercial contracting — a sales
agreement). Nothing in this module joins or merges the two.

No use case here asserts or implies legal validity of a right; this module
only records what an organization has entered.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.catalog_rights.domain.entities import (
    CatalogAsset,
    CatalogAssetArtist,
    CatalogOwnership,
    CatalogRelease,
    RightsApproval,
    RightsAuthorizedUse,
    RightsConflict,
    RightsContract,
    RightsContractParty,
    RightsCoverageRow,
    RightsStatusHistoryEntry,
    RightsTerritory,
)
from app.packages.catalog_rights.domain.errors import (
    ApprovalStateError,
    ConflictError,
    InvalidTransitionError,
    NotFoundError,
    OwnershipPercentageError,
    ValidationError,
    WarehouseTrackNotFoundError,
)


# ── Helpers ─────────────────────────────────────────────────────────────────


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
            source="catalog_rights.use_case",
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


def _assert_warehouse_track_exists(conn: duckdb.DuckDBPyConnection, warehouse_track_id: int) -> None:
    try:
        row = conn.execute(
            "SELECT 1 FROM dim_track WHERE id_track = ?", [warehouse_track_id]
        ).fetchone()
    except Exception:
        row = None
    if not row:
        raise WarehouseTrackNotFoundError(f"dim_track.id_track={warehouse_track_id} not found")


def _assert_artist_profile_in_org(
    conn: duckdb.DuckDBPyConnection, artist_profile_id: int, organization_id: int
) -> None:
    row = conn.execute(
        "SELECT 1 FROM app_artist_profile WHERE id = ? AND organization_id = ?",
        [artist_profile_id, organization_id],
    ).fetchone()
    if not row:
        raise ValidationError(
            f"artist_profile_id={artist_profile_id} not found in organization {organization_id}"
        )


def _record_status_history(
    conn: duckdb.DuckDBPyConnection,
    *,
    organization_id: int,
    entity_type: str,
    entity_id: int,
    from_status: Optional[str],
    to_status: str,
    actor: Optional[int],
    reason: Optional[str],
) -> None:
    now = _now()
    hid = _next_id(conn, "app_rights_status_history")
    conn.execute(
        f"INSERT INTO app_rights_status_history ({_HISTORY_COLS}) VALUES (?,?,?,?,?,?,?,?,?,?)",
        [hid, organization_id, entity_type, entity_id, from_status, to_status, actor, reason, now, now],
    )


# ── Column lists ──────────────────────────────────────────────────────────

_ASSET_COLS = (
    "id, organization_id, title, status, warehouse_track_id, artist_profile_id, "
    "created_by, created_at, updated_at"
)
_RELEASE_COLS = "id, organization_id, title, warehouse_album_id, created_by, created_at, updated_at"
_ASSET_ARTIST_COLS = "id, asset_id, artist_profile_id, role, created_at"
_OWNERSHIP_COLS = (
    "id, asset_id, organization_id, artist_profile_id, ownership_type, created_by, "
    "created_at, updated_at"
)
_CONTRACT_COLS = (
    "id, organization_id, asset_id, rights_type, status, exclusive, valid_from, "
    "valid_to, evidence_ref, created_by, created_at, updated_at"
)
_PARTY_COLS = (
    "id, contract_id, party_name, party_type, ownership_percentage, organization_id, "
    "artist_profile_id, created_at, updated_at"
)
_TERRITORY_COLS = "id, contract_id, territory_code, territory_name, created_at"
_USE_COLS = "id, contract_id, use_code, description, created_at"
_CONFLICT_COLS = (
    "id, organization_id, asset_id, rights_type, territory_code, status, details, "
    "resolved_by, resolved_at, created_at, updated_at"
)
_APPROVAL_COLS = (
    "id, contract_id, organization_id, status, approver_user_id, requested_by, notes, "
    "decided_at, created_at, updated_at"
)
_HISTORY_COLS = (
    "id, organization_id, entity_type, entity_id, from_status, to_status, actor, "
    "reason, at, created_at"
)

_RIGHTS_TYPES = ("master", "publishing", "neighboring", "other")
_CONTRACT_STATUSES = ("draft", "active", "expired", "archived", "disputed")
_ASSET_STATUSES = ("draft", "active", "archived")
_OWNERSHIP_TYPES = ("label", "artist", "publisher", "distributor", "other")
_PARTY_TYPES = ("organization", "artist", "external")


# ── Mappers ───────────────────────────────────────────────────────────────


def _map_asset(r: tuple) -> CatalogAsset:
    return CatalogAsset(
        id=int(r[0]), organization_id=int(r[1]), title=str(r[2]), status=str(r[3]),
        warehouse_track_id=int(r[4]) if r[4] is not None else None,
        artist_profile_id=int(r[5]) if r[5] is not None else None,
        created_by=int(r[6]) if r[6] is not None else None,
        created_at=r[7], updated_at=r[8],
    )


def _map_release(r: tuple) -> CatalogRelease:
    return CatalogRelease(
        id=int(r[0]), organization_id=int(r[1]), title=str(r[2]),
        warehouse_album_id=int(r[3]) if r[3] is not None else None,
        created_by=int(r[4]) if r[4] is not None else None,
        created_at=r[5], updated_at=r[6],
    )


def _map_asset_artist(r: tuple) -> CatalogAssetArtist:
    return CatalogAssetArtist(
        id=int(r[0]), asset_id=int(r[1]), artist_profile_id=int(r[2]),
        role=str(r[3]), created_at=r[4],
    )


def _map_ownership(r: tuple) -> CatalogOwnership:
    return CatalogOwnership(
        id=int(r[0]), asset_id=int(r[1]),
        organization_id=int(r[2]) if r[2] is not None else None,
        artist_profile_id=int(r[3]) if r[3] is not None else None,
        ownership_type=str(r[4]),
        created_by=int(r[5]) if r[5] is not None else None,
        created_at=r[6], updated_at=r[7],
    )


def _map_contract(r: tuple) -> RightsContract:
    return RightsContract(
        id=int(r[0]), organization_id=int(r[1]), asset_id=int(r[2]),
        rights_type=str(r[3]), status=str(r[4]), exclusive=bool(r[5]),
        valid_from=r[6], valid_to=r[7], evidence_ref=r[8],
        created_by=int(r[9]) if r[9] is not None else None,
        created_at=r[10], updated_at=r[11],
    )


def _map_party(r: tuple) -> RightsContractParty:
    return RightsContractParty(
        id=int(r[0]), contract_id=int(r[1]), party_name=str(r[2]), party_type=str(r[3]),
        ownership_percentage=float(r[4]),
        organization_id=int(r[5]) if r[5] is not None else None,
        artist_profile_id=int(r[6]) if r[6] is not None else None,
        created_at=r[7], updated_at=r[8],
    )


def _map_territory(r: tuple) -> RightsTerritory:
    return RightsTerritory(
        id=int(r[0]), contract_id=int(r[1]), territory_code=str(r[2]),
        territory_name=str(r[3]), created_at=r[4],
    )


def _map_use(r: tuple) -> RightsAuthorizedUse:
    return RightsAuthorizedUse(
        id=int(r[0]), contract_id=int(r[1]), use_code=str(r[2]), description=r[3],
        created_at=r[4],
    )


def _map_conflict(r: tuple) -> RightsConflict:
    return RightsConflict(
        id=int(r[0]), organization_id=int(r[1]), asset_id=int(r[2]), rights_type=str(r[3]),
        territory_code=str(r[4]), status=str(r[5]), details=r[6],
        resolved_by=int(r[7]) if r[7] is not None else None,
        resolved_at=r[8], created_at=r[9], updated_at=r[10],
    )


def _map_approval(r: tuple) -> RightsApproval:
    return RightsApproval(
        id=int(r[0]), contract_id=int(r[1]), organization_id=int(r[2]), status=str(r[3]),
        approver_user_id=int(r[4]) if r[4] is not None else None,
        requested_by=int(r[5]) if r[5] is not None else None,
        notes=r[6], decided_at=r[7], created_at=r[8], updated_at=r[9],
    )


def _map_history(r: tuple) -> RightsStatusHistoryEntry:
    return RightsStatusHistoryEntry(
        id=int(r[0]), organization_id=int(r[1]), entity_type=str(r[2]), entity_id=int(r[3]),
        from_status=r[4], to_status=str(r[5]),
        actor=int(r[6]) if r[6] is not None else None,
        reason=r[7], at=r[8], created_at=r[9],
    )


# ── CatalogAsset Use Cases ──────────────────────────────────────────────────


class CatalogAssetUseCases:
    """RegisterCatalogAsset, LinkWarehouseTrack, ListAssets, GetAsset."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def register(
        self,
        *,
        actor_user_id: int,
        organization_id: int,
        title: str,
        status: str = "active",
        warehouse_track_id: Optional[int] = None,
        artist_profile_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> CatalogAsset:
        if not title or not title.strip():
            raise ValidationError("title is required")
        if status not in _ASSET_STATUSES:
            raise ValidationError(f"status must be one of {_ASSET_STATUSES}")
        if warehouse_track_id is not None:
            _assert_warehouse_track_exists(self._conn, warehouse_track_id)
        if artist_profile_id is not None:
            _assert_artist_profile_in_org(self._conn, artist_profile_id, organization_id)

        now = _now()
        aid = _next_id(self._conn, "app_catalog_asset")
        self._conn.execute(
            f"INSERT INTO app_catalog_asset ({_ASSET_COLS}) VALUES (?,?,?,?,?,?,?,?,?)",
            [aid, organization_id, title.strip(), status, warehouse_track_id,
             artist_profile_id, actor_user_id, now, now],
        )
        _audit(
            self._conn, action="catalog_asset.registered", target_type="catalog_asset",
            target_id=str(aid), actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"title": title, "status": status}, request_id=request_id,
        )
        return self._get_or_raise(aid)

    def link_warehouse_track(
        self,
        asset_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        warehouse_track_id: int,
        request_id: Optional[str] = None,
    ) -> CatalogAsset:
        asset = self._get_or_raise_for_org(asset_id, organization_id)
        _assert_warehouse_track_exists(self._conn, warehouse_track_id)

        now = _now()
        self._conn.execute(
            "UPDATE app_catalog_asset SET warehouse_track_id = ?, updated_at = ? WHERE id = ?",
            [warehouse_track_id, now, asset_id],
        )
        _audit(
            self._conn, action="catalog_asset.warehouse_linked", target_type="catalog_asset",
            target_id=str(asset_id), actor_user_id=actor_user_id, organization_id=organization_id,
            previous_values={"warehouse_track_id": asset.warehouse_track_id},
            new_values={"warehouse_track_id": warehouse_track_id}, request_id=request_id,
        )
        return self._get_or_raise(asset_id)

    def list(
        self,
        *,
        organization_id: int,
        status: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[CatalogAsset], int]:
        conditions = ["organization_id = ?"]
        params: list[Any] = [organization_id]
        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        where = " AND ".join(conditions)
        total = int(
            self._conn.execute(
                f"SELECT COUNT(*) FROM app_catalog_asset WHERE {where}", params
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_ASSET_COLS} FROM app_catalog_asset WHERE {where} "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [_map_asset(r) for r in rows], total

    def get(self, asset_id: int, *, organization_id: int) -> CatalogAsset:
        return self._get_or_raise_for_org(asset_id, organization_id)

    def _get_or_raise(self, asset_id: int) -> CatalogAsset:
        row = self._conn.execute(
            f"SELECT {_ASSET_COLS} FROM app_catalog_asset WHERE id = ?", [asset_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"catalog_asset id={asset_id}")
        return _map_asset(row)

    def _get_or_raise_for_org(self, asset_id: int, organization_id: int) -> CatalogAsset:
        row = self._conn.execute(
            f"SELECT {_ASSET_COLS} FROM app_catalog_asset WHERE id = ? AND organization_id = ?",
            [asset_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"catalog_asset id={asset_id}")
        return _map_asset(row)


# ── CatalogRelease Use Cases ─────────────────────────────────────────────────


class CatalogReleaseUseCases:
    """CreateRelease, ListReleases, GetRelease."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        organization_id: int,
        title: str,
        warehouse_album_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> CatalogRelease:
        if not title or not title.strip():
            raise ValidationError("title is required")
        # warehouse_album_id is intentionally never validated against a
        # physical dim_album table: no such table currently exists in this
        # warehouse. It is stored purely as an optional, non-enforced
        # reference (see accepted-debt.md).
        now = _now()
        rid = _next_id(self._conn, "app_catalog_release")
        self._conn.execute(
            f"INSERT INTO app_catalog_release ({_RELEASE_COLS}) VALUES (?,?,?,?,?,?,?)",
            [rid, organization_id, title.strip(), warehouse_album_id, actor_user_id, now, now],
        )
        _audit(
            self._conn, action="catalog_release.created", target_type="catalog_release",
            target_id=str(rid), actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"title": title}, request_id=request_id,
        )
        return self._get_or_raise(rid)

    def list(
        self, *, organization_id: int, limit: int = 25, offset: int = 0
    ) -> tuple[list[CatalogRelease], int]:
        total = int(
            self._conn.execute(
                "SELECT COUNT(*) FROM app_catalog_release WHERE organization_id = ?",
                [organization_id],
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_RELEASE_COLS} FROM app_catalog_release WHERE organization_id = ? "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            [organization_id, limit, offset],
        ).fetchall()
        return [_map_release(r) for r in rows], total

    def get(self, release_id: int, *, organization_id: int) -> CatalogRelease:
        row = self._conn.execute(
            f"SELECT {_RELEASE_COLS} FROM app_catalog_release WHERE id = ? AND organization_id = ?",
            [release_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"catalog_release id={release_id}")
        return _map_release(row)

    def _get_or_raise(self, release_id: int) -> CatalogRelease:
        row = self._conn.execute(
            f"SELECT {_RELEASE_COLS} FROM app_catalog_release WHERE id = ?", [release_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"catalog_release id={release_id}")
        return _map_release(row)


# ── CatalogAssetArtist Use Cases ─────────────────────────────────────────────


class CatalogAssetArtistUseCases:
    """LinkAssetArtist — asset<->app_artist_profile linkage."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def link(
        self,
        asset_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        artist_profile_id: int,
        role: str = "primary",
        request_id: Optional[str] = None,
    ) -> CatalogAssetArtist:
        CatalogAssetUseCases(self._conn).get(asset_id, organization_id=organization_id)
        _assert_artist_profile_in_org(self._conn, artist_profile_id, organization_id)

        existing = self._conn.execute(
            "SELECT 1 FROM app_catalog_asset_artist WHERE asset_id = ? AND artist_profile_id = ?",
            [asset_id, artist_profile_id],
        ).fetchone()
        if existing:
            raise ConflictError(
                f"artist_profile {artist_profile_id} already linked to asset {asset_id}"
            )

        now = _now()
        link_id = _next_id(self._conn, "app_catalog_asset_artist")
        self._conn.execute(
            f"INSERT INTO app_catalog_asset_artist ({_ASSET_ARTIST_COLS}) VALUES (?,?,?,?,?)",
            [link_id, asset_id, artist_profile_id, role, now],
        )
        _audit(
            self._conn, action="catalog_asset_artist.linked", target_type="catalog_asset_artist",
            target_id=str(link_id), actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"asset_id": asset_id, "artist_profile_id": artist_profile_id},
            request_id=request_id,
        )
        row = self._conn.execute(
            f"SELECT {_ASSET_ARTIST_COLS} FROM app_catalog_asset_artist WHERE id = ?", [link_id]
        ).fetchone()
        return _map_asset_artist(row)

    def list_for_asset(self, asset_id: int) -> list[CatalogAssetArtist]:
        rows = self._conn.execute(
            f"SELECT {_ASSET_ARTIST_COLS} FROM app_catalog_asset_artist "
            "WHERE asset_id = ? ORDER BY id ASC",
            [asset_id],
        ).fetchall()
        return [_map_asset_artist(r) for r in rows]


# ── CatalogOwnership Use Cases ───────────────────────────────────────────────


class CatalogOwnershipUseCases:
    """RegisterOwnership — descriptive org/artist ownership link for an asset.

    Distinct from RightsContractParty: this records *who administers/holds*
    a catalog asset for organizational purposes, not a legally-binding
    percentage split (which lives in app_rights_contract_party).
    """

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def record(
        self,
        asset_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        ownership_type: str = "label",
        owner_organization_id: Optional[int] = None,
        artist_profile_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> CatalogOwnership:
        CatalogAssetUseCases(self._conn).get(asset_id, organization_id=organization_id)
        if ownership_type not in _OWNERSHIP_TYPES:
            raise ValidationError(f"ownership_type must be one of {_OWNERSHIP_TYPES}")
        if owner_organization_id is None and artist_profile_id is None:
            raise ValidationError("owner_organization_id or artist_profile_id is required")
        if artist_profile_id is not None:
            _assert_artist_profile_in_org(self._conn, artist_profile_id, organization_id)

        now = _now()
        oid = _next_id(self._conn, "app_catalog_ownership")
        self._conn.execute(
            f"INSERT INTO app_catalog_ownership ({_OWNERSHIP_COLS}) VALUES (?,?,?,?,?,?,?,?)",
            [oid, asset_id, owner_organization_id, artist_profile_id, ownership_type,
             actor_user_id, now, now],
        )
        _audit(
            self._conn, action="catalog_ownership.recorded", target_type="catalog_ownership",
            target_id=str(oid), actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"asset_id": asset_id, "ownership_type": ownership_type},
            request_id=request_id,
        )
        row = self._conn.execute(
            f"SELECT {_OWNERSHIP_COLS} FROM app_catalog_ownership WHERE id = ?", [oid]
        ).fetchone()
        return _map_ownership(row)

    def list_for_asset(self, asset_id: int) -> list[CatalogOwnership]:
        rows = self._conn.execute(
            f"SELECT {_OWNERSHIP_COLS} FROM app_catalog_ownership WHERE asset_id = ? ORDER BY id ASC",
            [asset_id],
        ).fetchall()
        return [_map_ownership(r) for r in rows]


# ── RightsContract Use Cases ─────────────────────────────────────────────────


class RightsContractUseCases:
    """CreateRightsContract, ArchiveContract, ListContracts, GetContract.

    A rights contract is always scoped to a single app_catalog_asset (never
    a raw dim_track row) and is never the same table as
    app_commercial_contract (Spec 017 CRM sales contracting).
    """

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        organization_id: int,
        asset_id: int,
        rights_type: str,
        valid_from: date,
        valid_to: Optional[date] = None,
        exclusive: bool = False,
        evidence_ref: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> RightsContract:
        CatalogAssetUseCases(self._conn).get(asset_id, organization_id=organization_id)
        if rights_type not in _RIGHTS_TYPES:
            raise ValidationError(f"rights_type must be one of {_RIGHTS_TYPES}")
        if valid_to is not None and valid_to < valid_from:
            raise ValidationError("valid_to must be on or after valid_from")

        now = _now()
        cid = _next_id(self._conn, "app_rights_contract")
        self._conn.execute(
            f"INSERT INTO app_rights_contract ({_CONTRACT_COLS}) "
            "VALUES (?,?,?,?,'draft',?,?,?,?,?,?,?)",
            [cid, organization_id, asset_id, rights_type, exclusive, valid_from, valid_to,
             evidence_ref, actor_user_id, now, now],
        )
        _record_status_history(
            self._conn, organization_id=organization_id, entity_type="rights_contract",
            entity_id=cid, from_status=None, to_status="draft", actor=actor_user_id,
            reason="created",
        )
        _audit(
            self._conn, action="rights_contract.created", target_type="rights_contract",
            target_id=str(cid), actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"asset_id": asset_id, "rights_type": rights_type, "status": "draft"},
            request_id=request_id,
        )
        return self._get_or_raise(cid)

    def archive(
        self,
        contract_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> RightsContract:
        contract = self._get_or_raise_for_org(contract_id, organization_id)
        if contract.status == "archived":
            raise InvalidTransitionError("Contract is already archived")

        now = _now()
        self._conn.execute(
            "UPDATE app_rights_contract SET status = 'archived', updated_at = ? WHERE id = ?",
            [now, contract_id],
        )
        _record_status_history(
            self._conn, organization_id=organization_id, entity_type="rights_contract",
            entity_id=contract_id, from_status=contract.status, to_status="archived",
            actor=actor_user_id, reason=reason,
        )
        _audit(
            self._conn, action="rights_contract.archived", target_type="rights_contract",
            target_id=str(contract_id), actor_user_id=actor_user_id, organization_id=organization_id,
            previous_values={"status": contract.status}, new_values={"status": "archived"},
            reason=reason, request_id=request_id,
        )
        return self._get_or_raise(contract_id)

    def list(
        self,
        *,
        organization_id: int,
        asset_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[RightsContract], int]:
        conditions = ["organization_id = ?"]
        params: list[Any] = [organization_id]
        if asset_id is not None:
            conditions.append("asset_id = ?")
            params.append(asset_id)
        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        where = " AND ".join(conditions)
        total = int(
            self._conn.execute(
                f"SELECT COUNT(*) FROM app_rights_contract WHERE {where}", params
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_CONTRACT_COLS} FROM app_rights_contract WHERE {where} "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [_map_contract(r) for r in rows], total

    def get(self, contract_id: int, *, organization_id: int) -> RightsContract:
        return self._get_or_raise_for_org(contract_id, organization_id)

    def _mark_disputed(
        self, contract_id: int, *, organization_id: int, actor_user_id: Optional[int], reason: str
    ) -> None:
        contract = self._get_or_raise(contract_id)
        if contract.status in ("archived", "disputed"):
            return
        now = _now()
        self._conn.execute(
            "UPDATE app_rights_contract SET status = 'disputed', updated_at = ? WHERE id = ?",
            [now, contract_id],
        )
        _record_status_history(
            self._conn, organization_id=organization_id, entity_type="rights_contract",
            entity_id=contract_id, from_status=contract.status, to_status="disputed",
            actor=actor_user_id, reason=reason,
        )
        _audit(
            self._conn, action="rights_contract.disputed", target_type="rights_contract",
            target_id=str(contract_id), actor_user_id=actor_user_id, organization_id=organization_id,
            previous_values={"status": contract.status}, new_values={"status": "disputed"},
            reason=reason,
        )

    def _get_or_raise(self, contract_id: int) -> RightsContract:
        row = self._conn.execute(
            f"SELECT {_CONTRACT_COLS} FROM app_rights_contract WHERE id = ?", [contract_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"rights_contract id={contract_id}")
        return _map_contract(row)

    def _get_or_raise_for_org(self, contract_id: int, organization_id: int) -> RightsContract:
        row = self._conn.execute(
            f"SELECT {_CONTRACT_COLS} FROM app_rights_contract WHERE id = ? AND organization_id = ?",
            [contract_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"rights_contract id={contract_id}")
        return _map_contract(row)


# ── RightsContractParty Use Cases ────────────────────────────────────────────


class RightsContractPartyUseCases:
    """AddContractParty — triggers DetectOverlap after every insert."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def add(
        self,
        contract_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        party_name: str,
        party_type: str = "external",
        ownership_percentage: float,
        party_organization_id: Optional[int] = None,
        artist_profile_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> tuple[RightsContractParty, list[RightsConflict]]:
        contract = RightsContractUseCases(self._conn).get(contract_id, organization_id=organization_id)
        if not party_name or not party_name.strip():
            raise ValidationError("party_name is required")
        if party_type not in _PARTY_TYPES:
            raise ValidationError(f"party_type must be one of {_PARTY_TYPES}")
        if ownership_percentage is None or not (0 < ownership_percentage <= 100):
            raise OwnershipPercentageError("ownership_percentage must be in (0, 100]")

        now = _now()
        pid = _next_id(self._conn, "app_rights_contract_party")
        self._conn.execute(
            f"INSERT INTO app_rights_contract_party ({_PARTY_COLS}) VALUES (?,?,?,?,?,?,?,?,?)",
            [pid, contract_id, party_name.strip(), party_type, float(ownership_percentage),
             party_organization_id, artist_profile_id, now, now],
        )
        _audit(
            self._conn, action="rights_contract_party.added", target_type="rights_contract_party",
            target_id=str(pid), actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"contract_id": contract_id, "party_name": party_name,
                        "ownership_percentage": ownership_percentage},
            request_id=request_id,
        )
        row = self._conn.execute(
            f"SELECT {_PARTY_COLS} FROM app_rights_contract_party WHERE id = ?", [pid]
        ).fetchone()
        party = _map_party(row)

        conflicts = RightsConflictUseCases(self._conn).detect_overlap(
            asset_id=contract.asset_id, rights_type=contract.rights_type,
            organization_id=organization_id, actor_user_id=actor_user_id, request_id=request_id,
        )
        return party, conflicts

    def list_for_contract(self, contract_id: int) -> list[RightsContractParty]:
        rows = self._conn.execute(
            f"SELECT {_PARTY_COLS} FROM app_rights_contract_party "
            "WHERE contract_id = ? ORDER BY id ASC",
            [contract_id],
        ).fetchall()
        return [_map_party(r) for r in rows]


# ── RightsTerritory Use Cases ────────────────────────────────────────────────


class RightsTerritoryUseCases:
    """SetTerritories — full replace of a contract's territory scope."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def set_territories(
        self,
        contract_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        territories: list[dict[str, str]],
        request_id: Optional[str] = None,
    ) -> tuple[list[RightsTerritory], list[RightsConflict]]:
        contract = RightsContractUseCases(self._conn).get(contract_id, organization_id=organization_id)
        for t in territories:
            if not t.get("territory_code") or not t.get("territory_name"):
                raise ValidationError("territory_code and territory_name are required")

        now = _now()
        self._conn.execute(
            "DELETE FROM app_rights_territory WHERE contract_id = ?", [contract_id]
        )
        for t in territories:
            tid = _next_id(self._conn, "app_rights_territory")
            self._conn.execute(
                f"INSERT INTO app_rights_territory ({_TERRITORY_COLS}) VALUES (?,?,?,?,?)",
                [tid, contract_id, t["territory_code"].strip().upper(),
                 t["territory_name"].strip(), now],
            )
        _audit(
            self._conn, action="rights_territory.set", target_type="rights_contract",
            target_id=str(contract_id), actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"territories": [t["territory_code"] for t in territories]},
            request_id=request_id,
        )
        conflicts = RightsConflictUseCases(self._conn).detect_overlap(
            asset_id=contract.asset_id, rights_type=contract.rights_type,
            organization_id=organization_id, actor_user_id=actor_user_id, request_id=request_id,
        )
        return self.list_for_contract(contract_id), conflicts

    def list_for_contract(self, contract_id: int) -> list[RightsTerritory]:
        rows = self._conn.execute(
            f"SELECT {_TERRITORY_COLS} FROM app_rights_territory WHERE contract_id = ? ORDER BY id ASC",
            [contract_id],
        ).fetchall()
        return [_map_territory(r) for r in rows]


# ── RightsAuthorizedUse Use Cases ────────────────────────────────────────────


class RightsAuthorizedUseUseCases:
    """SetAuthorizedUses — full replace of a contract's authorized-use list."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def set_uses(
        self,
        contract_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        uses: list[dict[str, Optional[str]]],
        request_id: Optional[str] = None,
    ) -> list[RightsAuthorizedUse]:
        RightsContractUseCases(self._conn).get(contract_id, organization_id=organization_id)
        for u in uses:
            if not u.get("use_code"):
                raise ValidationError("use_code is required")

        now = _now()
        self._conn.execute(
            "DELETE FROM app_rights_authorized_use WHERE contract_id = ?", [contract_id]
        )
        for u in uses:
            uid = _next_id(self._conn, "app_rights_authorized_use")
            self._conn.execute(
                f"INSERT INTO app_rights_authorized_use ({_USE_COLS}) VALUES (?,?,?,?,?)",
                [uid, contract_id, u["use_code"].strip(), u.get("description"), now],
            )
        _audit(
            self._conn, action="rights_authorized_use.set", target_type="rights_contract",
            target_id=str(contract_id), actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"uses": [u["use_code"] for u in uses]}, request_id=request_id,
        )
        return self.list_for_contract(contract_id)

    def list_for_contract(self, contract_id: int) -> list[RightsAuthorizedUse]:
        rows = self._conn.execute(
            f"SELECT {_USE_COLS} FROM app_rights_authorized_use WHERE contract_id = ? ORDER BY id ASC",
            [contract_id],
        ).fetchall()
        return [_map_use(r) for r in rows]


# ── RightsApproval Use Cases ─────────────────────────────────────────────────


class RightsApprovalUseCases:
    """SubmitForApproval, ApproveContract (approve/reject)."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def submit(
        self,
        contract_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        request_id: Optional[str] = None,
    ) -> RightsApproval:
        contract = RightsContractUseCases(self._conn).get(contract_id, organization_id=organization_id)
        if contract.status not in ("draft", "disputed"):
            raise ValidationError(
                f"Cannot submit contract with status '{contract.status}' for approval"
            )
        existing_pending = self._conn.execute(
            "SELECT 1 FROM app_rights_approval WHERE contract_id = ? AND status = 'pending'",
            [contract_id],
        ).fetchone()
        if existing_pending:
            raise ConflictError(f"Contract {contract_id} already has a pending approval")

        now = _now()
        apid = _next_id(self._conn, "app_rights_approval")
        self._conn.execute(
            f"INSERT INTO app_rights_approval ({_APPROVAL_COLS}) "
            "VALUES (?,?,?,'pending',NULL,?,NULL,NULL,?,?)",
            [apid, contract_id, organization_id, actor_user_id, now, now],
        )
        _audit(
            self._conn, action="rights_approval.submitted", target_type="rights_approval",
            target_id=str(apid), actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"contract_id": contract_id, "status": "pending"}, request_id=request_id,
        )
        row = self._conn.execute(
            f"SELECT {_APPROVAL_COLS} FROM app_rights_approval WHERE id = ?", [apid]
        ).fetchone()
        return _map_approval(row)

    def decide(
        self,
        contract_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        approved: bool,
        notes: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> RightsApproval:
        contract = RightsContractUseCases(self._conn).get(contract_id, organization_id=organization_id)
        row = self._conn.execute(
            f"SELECT {_APPROVAL_COLS} FROM app_rights_approval "
            "WHERE contract_id = ? AND organization_id = ? AND status = 'pending' "
            "ORDER BY id DESC LIMIT 1",
            [contract_id, organization_id],
        ).fetchone()
        if not row:
            raise ApprovalStateError(
                f"Contract {contract_id} has no pending approval — call SubmitForApproval first"
            )
        approval = _map_approval(row)

        now = _now()
        new_status = "approved" if approved else "rejected"
        self._conn.execute(
            "UPDATE app_rights_approval SET status = ?, approver_user_id = ?, notes = ?, "
            "decided_at = ?, updated_at = ? WHERE id = ?",
            [new_status, actor_user_id, notes, now, now, approval.id],
        )
        if approved:
            self._conn.execute(
                "UPDATE app_rights_contract SET status = 'active', updated_at = ? WHERE id = ?",
                [now, contract_id],
            )
            _record_status_history(
                self._conn, organization_id=organization_id, entity_type="rights_contract",
                entity_id=contract_id, from_status=contract.status, to_status="active",
                actor=actor_user_id, reason="approved",
            )
        _audit(
            self._conn, action=f"rights_approval.{new_status}", target_type="rights_approval",
            target_id=str(approval.id), actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"status": new_status}, reason=notes, request_id=request_id,
        )
        row = self._conn.execute(
            f"SELECT {_APPROVAL_COLS} FROM app_rights_approval WHERE id = ?", [approval.id]
        ).fetchone()
        return _map_approval(row)

    def list_for_contract(self, contract_id: int) -> list[RightsApproval]:
        rows = self._conn.execute(
            f"SELECT {_APPROVAL_COLS} FROM app_rights_approval WHERE contract_id = ? ORDER BY id ASC",
            [contract_id],
        ).fetchall()
        return [_map_approval(r) for r in rows]


# ── Overlap detection (shared) ───────────────────────────────────────────────

_FAR_FUTURE = date(9998, 12, 31)


@dataclass
class _Interval:
    contract_id: int
    start: date
    end: date
    percentage: float


def _sweep_max_overlap(intervals: list[_Interval]) -> tuple[float, set[int]]:
    """Returns (max concurrent percentage, contract ids active at that peak)."""
    events: list[tuple[date, int, int, float]] = []
    for iv in intervals:
        events.append((iv.start, 1, iv.contract_id, iv.percentage))
        events.append((iv.end + timedelta(days=1), 0, iv.contract_id, -iv.percentage))
    events.sort(key=lambda e: (e[0], e[1]))

    active: dict[int, float] = {}
    max_sum = 0.0
    max_active: set[int] = set()
    for _, _, cid, delta in events:
        if delta > 0:
            active[cid] = delta
        else:
            active.pop(cid, None)
        current = sum(active.values())
        if current > max_sum:
            max_sum = current
            max_active = set(active.keys())
    return max_sum, max_active


class RightsConflictUseCases:
    """DetectOverlap, OpenConflict, ResolveConflict, ListConflicts, GetConflict."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def _compute_overlaps(
        self, asset_id: int, rights_type: str
    ) -> dict[str, tuple[float, set[int]]]:
        """For every distinct territory applicable to (asset_id, rights_type),
        compute the maximum concurrent ownership_percentage claimed across all
        non-archived contracts whose applicable period overlaps."""
        contracts = self._conn.execute(
            "SELECT id, valid_from, valid_to FROM app_rights_contract "
            "WHERE asset_id = ? AND rights_type = ? AND status != 'archived'",
            [asset_id, rights_type],
        ).fetchall()
        if not contracts:
            return {}

        contract_territories: dict[int, set[str]] = {}
        contract_percentage: dict[int, float] = {}
        contract_period: dict[int, tuple[date, date]] = {}
        territory_universe: set[str] = set()

        for cid, valid_from, valid_to in contracts:
            cid = int(cid)
            trows = self._conn.execute(
                "SELECT territory_code FROM app_rights_territory WHERE contract_id = ?", [cid]
            ).fetchall()
            codes = {str(t[0]) for t in trows} or {"WORLD"}
            contract_territories[cid] = codes
            territory_universe |= {c for c in codes if c != "WORLD"}

            pct_row = self._conn.execute(
                "SELECT COALESCE(SUM(ownership_percentage), 0) FROM app_rights_contract_party "
                "WHERE contract_id = ?",
                [cid],
            ).fetchone()
            contract_percentage[cid] = float(pct_row[0])
            contract_period[cid] = (valid_from, valid_to if valid_to else _FAR_FUTURE)

        if not territory_universe:
            # All contracts are WORLD-scoped (or no explicit territories anywhere).
            territory_universe = {"WORLD"}

        results: dict[str, tuple[float, set[int]]] = {}
        for territory_code in territory_universe:
            applicable = [
                _Interval(cid, contract_period[cid][0], contract_period[cid][1], contract_percentage[cid])
                for cid, codes in contract_territories.items()
                if territory_code in codes or "WORLD" in codes
            ]
            if not applicable:
                continue
            max_sum, max_active = _sweep_max_overlap(applicable)
            if max_sum > 0:
                results[territory_code] = (max_sum, max_active)
        return results

    def detect_overlap(
        self,
        *,
        asset_id: int,
        rights_type: str,
        organization_id: int,
        actor_user_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> list[RightsConflict]:
        overlaps = self._compute_overlaps(asset_id, rights_type)
        opened: list[RightsConflict] = []
        for territory_code, (max_sum, contract_ids) in overlaps.items():
            if round(max_sum, 4) > 100.0:
                details = (
                    f"Contracts {sorted(contract_ids)} claim {max_sum:.2f}% concurrently "
                    f"in territory {territory_code} for rights_type={rights_type}"
                )
                conflict = self._open_or_refresh(
                    asset_id=asset_id, rights_type=rights_type, territory_code=territory_code,
                    organization_id=organization_id, details=details, request_id=request_id,
                    actor_user_id=actor_user_id,
                )
                opened.append(conflict)
                for cid in contract_ids:
                    RightsContractUseCases(self._conn)._mark_disputed(
                        cid, organization_id=organization_id, actor_user_id=actor_user_id,
                        reason=f"Ownership overlap conflict in {territory_code}",
                    )
        return opened

    def open_conflict(
        self,
        *,
        actor_user_id: int,
        organization_id: int,
        asset_id: int,
        rights_type: str,
        territory_code: str,
        details: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> RightsConflict:
        CatalogAssetUseCases(self._conn).get(asset_id, organization_id=organization_id)
        if rights_type not in _RIGHTS_TYPES:
            raise ValidationError(f"rights_type must be one of {_RIGHTS_TYPES}")
        return self._open_or_refresh(
            asset_id=asset_id, rights_type=rights_type, territory_code=territory_code.strip().upper(),
            organization_id=organization_id, details=details or "Manually opened",
            request_id=request_id, actor_user_id=actor_user_id,
        )

    def _open_or_refresh(
        self,
        *,
        asset_id: int,
        rights_type: str,
        territory_code: str,
        organization_id: int,
        details: str,
        request_id: Optional[str],
        actor_user_id: Optional[int] = None,
    ) -> RightsConflict:
        now = _now()
        existing = self._conn.execute(
            f"SELECT {_CONFLICT_COLS} FROM app_rights_conflict WHERE asset_id = ? "
            "AND rights_type = ? AND territory_code = ? AND status = 'open'",
            [asset_id, rights_type, territory_code],
        ).fetchone()
        if existing:
            conflict_id = int(existing[0])
            self._conn.execute(
                "UPDATE app_rights_conflict SET details = ?, updated_at = ? WHERE id = ?",
                [details, now, conflict_id],
            )
        else:
            conflict_id = _next_id(self._conn, "app_rights_conflict")
            self._conn.execute(
                f"INSERT INTO app_rights_conflict ({_CONFLICT_COLS}) "
                "VALUES (?,?,?,?,?,'open',?,NULL,NULL,?,?)",
                [conflict_id, organization_id, asset_id, rights_type, territory_code,
                 details, now, now],
            )
            _audit(
                self._conn, action="rights_conflict.opened", target_type="rights_conflict",
                target_id=str(conflict_id), actor_user_id=actor_user_id, organization_id=organization_id,
                new_values={"asset_id": asset_id, "rights_type": rights_type,
                            "territory_code": territory_code},
                reason=details, request_id=request_id,
            )
        row = self._conn.execute(
            f"SELECT {_CONFLICT_COLS} FROM app_rights_conflict WHERE id = ?", [conflict_id]
        ).fetchone()
        return _map_conflict(row)

    def resolve(
        self,
        conflict_id: int,
        *,
        actor_user_id: int,
        organization_id: int,
        resolution: str,
        notes: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> RightsConflict:
        if resolution not in ("resolved", "dismissed"):
            raise ValidationError("resolution must be 'resolved' or 'dismissed'")
        row = self._conn.execute(
            f"SELECT {_CONFLICT_COLS} FROM app_rights_conflict WHERE id = ? AND organization_id = ?",
            [conflict_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"rights_conflict id={conflict_id}")
        conflict = _map_conflict(row)
        if conflict.status != "open":
            raise InvalidTransitionError(f"Conflict {conflict_id} is already {conflict.status}")

        now = _now()
        details = f"{conflict.details or ''} | resolution note: {notes}".strip(" |") if notes else conflict.details
        self._conn.execute(
            "UPDATE app_rights_conflict SET status = ?, resolved_by = ?, resolved_at = ?, "
            "details = ?, updated_at = ? WHERE id = ?",
            [resolution, actor_user_id, now, details, now, conflict_id],
        )
        _audit(
            self._conn, action=f"rights_conflict.{resolution}", target_type="rights_conflict",
            target_id=str(conflict_id), actor_user_id=actor_user_id, organization_id=organization_id,
            previous_values={"status": "open"}, new_values={"status": resolution},
            reason=notes, request_id=request_id,
        )
        row = self._conn.execute(
            f"SELECT {_CONFLICT_COLS} FROM app_rights_conflict WHERE id = ?", [conflict_id]
        ).fetchone()
        return _map_conflict(row)

    def list(
        self,
        *,
        organization_id: int,
        asset_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> list[RightsConflict]:
        conditions = ["organization_id = ?"]
        params: list[Any] = [organization_id]
        if asset_id is not None:
            conditions.append("asset_id = ?")
            params.append(asset_id)
        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        where = " AND ".join(conditions)
        rows = self._conn.execute(
            f"SELECT {_CONFLICT_COLS} FROM app_rights_conflict WHERE {where} ORDER BY id DESC",
            params,
        ).fetchall()
        return [_map_conflict(r) for r in rows]

    def get(self, conflict_id: int, *, organization_id: int) -> RightsConflict:
        row = self._conn.execute(
            f"SELECT {_CONFLICT_COLS} FROM app_rights_conflict WHERE id = ? AND organization_id = ?",
            [conflict_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"rights_conflict id={conflict_id}")
        return _map_conflict(row)


# ── RightsCoverage Use Cases ─────────────────────────────────────────────────


class RightsCoverageUseCases:
    """QueryRightsCoverage — read-only aggregation, not a persisted table."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def query(
        self, asset_id: int, *, organization_id: int, rights_type: Optional[str] = None
    ) -> list[RightsCoverageRow]:
        CatalogAssetUseCases(self._conn).get(asset_id, organization_id=organization_id)
        if rights_type is not None and rights_type not in _RIGHTS_TYPES:
            raise ValidationError(f"rights_type must be one of {_RIGHTS_TYPES}")

        types_to_check: list[str]
        if rights_type is not None:
            types_to_check = [rights_type]
        else:
            rows = self._conn.execute(
                "SELECT DISTINCT rights_type FROM app_rights_contract WHERE asset_id = ?",
                [asset_id],
            ).fetchall()
            types_to_check = [str(r[0]) for r in rows]

        conflict_uc = RightsConflictUseCases(self._conn)
        out: list[RightsCoverageRow] = []
        for rt in types_to_check:
            overlaps = conflict_uc._compute_overlaps(asset_id, rt)
            open_conflicts = {
                c.territory_code for c in conflict_uc.list(
                    organization_id=organization_id, asset_id=asset_id, status="open"
                ) if c.rights_type == rt
            }
            for territory_code, (max_sum, contract_ids) in overlaps.items():
                out.append(
                    RightsCoverageRow(
                        asset_id=asset_id, rights_type=rt, territory_code=territory_code,
                        total_percentage=round(max_sum, 4), contract_count=len(contract_ids),
                        has_conflict=(round(max_sum, 4) > 100.0) or territory_code in open_conflicts,
                    )
                )
        return out


# ── RightsHistory Use Cases ──────────────────────────────────────────────────


class RightsHistoryUseCases:
    """GetContractHistory — read-only, append-only status trail."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def get_contract_history(
        self, contract_id: int, *, organization_id: int
    ) -> list[RightsStatusHistoryEntry]:
        RightsContractUseCases(self._conn).get(contract_id, organization_id=organization_id)
        rows = self._conn.execute(
            f"SELECT {_HISTORY_COLS} FROM app_rights_status_history "
            "WHERE entity_type = 'rights_contract' AND entity_id = ? AND organization_id = ? "
            "ORDER BY at ASC, id ASC",
            [contract_id, organization_id],
        ).fetchall()
        return [_map_history(r) for r in rows]
