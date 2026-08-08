"""Catalog publishing use cases — Spec 031.

Publish policy for warehouse tracks:
  1. Prefer an existing ``warehouse_track_id`` already on the submission track.
  2. Otherwise create a synthetic ``dim_track`` row with id >= 9_000_000 and
     title prefix ``[DEMO-SUBMIT]`` — never touch imported ids < 100000.
  3. Register ``app_track_audio_source`` with provider ``local_published`` and
     playable_url pointing at ``/api/v1/media/{id}/content``.
  Do NOT mint analytics/fact events on publish.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.catalog_publishing.domain.errors import (
    ConflictError,
    IdempotencyConflictError,
    InvalidTransitionError,
    MediaValidationError,
    NotFoundError,
    RightsGateError,
    ValidationError,
)
from app.packages.catalog_publishing.domain.state_machine import transition
from app.packages.catalog_publishing.infrastructure.local_media_storage import (
    LocalMediaStorageProvider,
)
from app.packages.catalog_publishing.infrastructure.schema import (
    DEMO_TRACK_TITLE_PREFIX,
    DEMO_WAREHOUSE_TRACK_ID_MIN,
)

HUNDRED = Decimal("100")
ZERO = Decimal("0")

_SUB_COLS = (
    "id", "organization_id", "artist_profile_id", "release_type", "title",
    "version", "label_name", "genre", "language", "explicit",
    "planned_release_date", "actual_release_date", "upc", "cover_media_id",
    "status", "created_by", "reviewer_id", "rights_contract_id",
    "catalog_asset_id", "catalog_release_id", "reject_reason", "withdraw_reason",
    "is_demo", "scheduled_at", "published_at", "idempotency_key",
    "created_at", "updated_at",
)
_TRACK_COLS = (
    "id", "submission_id", "title", "version", "track_number", "disc_number",
    "primary_artist_id", "duration_ms", "isrc", "explicit", "audio_media_id",
    "catalog_asset_id", "rights_contract_id", "warehouse_track_id",
    "validation_status", "sort_order", "created_at", "updated_at",
)
_MEDIA_COLS = (
    "id", "organization_id", "kind", "content_type", "original_filename",
    "stored_name", "relative_path", "byte_size", "sha256", "duration_ms",
    "width", "height", "status", "created_by", "created_at",
)


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    return int(conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()[0])


def _now() -> datetime:
    return utc_now()


def _table_exists(conn: duckdb.DuckDBPyConnection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_name = ? LIMIT 1",
        [name],
    ).fetchone()
    return row is not None


def _row_dict(cols: tuple[str, ...], row: tuple) -> dict[str, Any]:
    return {c: row[i] for i, c in enumerate(cols)}


def _dec(v: Any) -> Decimal:
    if isinstance(v, Decimal):
        return v
    if v is None:
        return ZERO
    return Decimal(str(v))


class CatalogPublishingUseCases:
    def __init__(
        self,
        conn: duckdb.DuckDBPyConnection,
        media: Optional[LocalMediaStorageProvider] = None,
    ) -> None:
        self._conn = conn
        self._media = media or LocalMediaStorageProvider()

    # ── helpers ────────────────────────────────────────────────────────────

    def _get_submission(
        self, submission_id: int, *, org_id: Optional[int] = None
    ) -> dict[str, Any]:
        row = self._conn.execute(
            f"SELECT {', '.join(_SUB_COLS)} FROM app_release_submission WHERE id = ?",
            [submission_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"Submission {submission_id} not found")
        d = _row_dict(_SUB_COLS, row)
        if org_id is not None and int(d["organization_id"]) != int(org_id):
            raise NotFoundError(f"Submission {submission_id} not found")
        return d

    def _assert_editable(self, sub: dict[str, Any]) -> None:
        if sub["status"] not in ("draft", "changes_requested"):
            raise ValidationError(
                f"Submission status {sub['status']!r} is locked for metadata edits"
            )

    def _tracks(self, submission_id: int) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            f"""
            SELECT {', '.join(_TRACK_COLS)} FROM app_release_submission_track
            WHERE submission_id = ?
            ORDER BY sort_order, track_number, id
            """,
            [submission_id],
        ).fetchall()
        return [_row_dict(_TRACK_COLS, r) for r in rows]

    def _add_issue(
        self,
        *,
        submission_id: int,
        severity: str,
        code: str,
        message: str,
        field_ref: Optional[str] = None,
        review_id: Optional[int] = None,
    ) -> None:
        iid = _next_id(self._conn, "app_release_review_issue")
        self._conn.execute(
            """
            INSERT INTO app_release_review_issue
                (id, review_id, submission_id, severity, code, message, field_ref,
                 resolved, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, FALSE, ?)
            """,
            [iid, review_id, submission_id, severity, code, message, field_ref, _now()],
        )

    def _record_event(
        self,
        submission_id: int,
        event_type: str,
        actor_user_id: int,
        payload: Optional[dict] = None,
    ) -> None:
        eid = _next_id(self._conn, "app_catalog_publication_event")
        self._conn.execute(
            """
            INSERT INTO app_catalog_publication_event
                (id, submission_id, event_type, payload, actor_user_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                eid,
                submission_id,
                event_type,
                json.dumps(payload or {}),
                actor_user_id,
                _now(),
            ],
        )

    def _get_media(self, media_id: int) -> dict[str, Any]:
        row = self._conn.execute(
            f"SELECT {', '.join(_MEDIA_COLS)} FROM app_media_asset WHERE id = ?",
            [media_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"Media {media_id} not found")
        return _row_dict(_MEDIA_COLS, row)

    # ── drafts / metadata ──────────────────────────────────────────────────

    def create_draft(
        self,
        *,
        actor_user_id: int,
        organization_id: int,
        artist_profile_id: int,
        title: str,
        release_type: str = "single",
        idempotency_key: Optional[str] = None,
        is_demo: bool = False,
        **meta: Any,
    ) -> dict[str, Any]:
        if not (title or "").strip():
            raise ValidationError("title is required")
        if release_type not in ("single", "ep", "album", "compilation"):
            raise ValidationError(f"Invalid release_type: {release_type}")
        if idempotency_key:
            existing = self._conn.execute(
                "SELECT id FROM app_release_submission WHERE idempotency_key = ?",
                [idempotency_key],
            ).fetchone()
            if existing:
                return self._get_submission(int(existing[0]), org_id=organization_id)

        now = _now()
        sid = _next_id(self._conn, "app_release_submission")
        self._conn.execute(
            f"""
            INSERT INTO app_release_submission
                ({', '.join(_SUB_COLS)})
            VALUES ({', '.join('?' for _ in _SUB_COLS)})
            """,
            [
                sid, organization_id, artist_profile_id, release_type, title.strip(),
                meta.get("version"), meta.get("label_name"), meta.get("genre"),
                meta.get("language"), bool(meta.get("explicit", False)),
                meta.get("planned_release_date"), meta.get("actual_release_date"),
                meta.get("upc"), None, "draft", actor_user_id, None,
                meta.get("rights_contract_id"), None, None, None, None,
                bool(is_demo), None, None, idempotency_key, now, now,
            ],
        )
        hist = _next_id(self._conn, "app_release_status_history")
        self._conn.execute(
            """
            INSERT INTO app_release_status_history
                (id, submission_id, from_status, to_status, actor_user_id, reason, created_at)
            VALUES (?, ?, 'draft', 'draft', ?, 'created', ?)
            """,
            [hist, sid, actor_user_id, now],
        )
        return self._get_submission(sid)

    def update_metadata(
        self,
        *,
        submission_id: int,
        organization_id: int,
        actor_user_id: int,
        **fields: Any,
    ) -> dict[str, Any]:
        sub = self._get_submission(submission_id, org_id=organization_id)
        self._assert_editable(sub)
        allowed = {
            "title", "version", "label_name", "genre", "language", "explicit",
            "planned_release_date", "actual_release_date", "upc", "release_type",
            "rights_contract_id", "cover_media_id",
        }
        changed = False
        for k, v in fields.items():
            if k in allowed and v is not None:
                sub[k] = v
                changed = True
        if not changed:
            return sub
        sub["updated_at"] = _now()
        from app.packages.catalog_publishing.domain.state_machine import (
            _SUB_COLS,
            _rewrite_submission,
        )

        _rewrite_submission(self._conn, {c: sub.get(c) for c in _SUB_COLS})
        return self._get_submission(submission_id)

    def add_track(
        self,
        *,
        submission_id: int,
        organization_id: int,
        title: str,
        track_number: int = 1,
        **fields: Any,
    ) -> dict[str, Any]:
        sub = self._get_submission(submission_id, org_id=organization_id)
        self._assert_editable(sub)
        if not (title or "").strip():
            raise ValidationError("track title is required")
        now = _now()
        tid = _next_id(self._conn, "app_release_submission_track")
        sort_order = int(fields.get("sort_order", track_number * 10))
        self._conn.execute(
            f"""
            INSERT INTO app_release_submission_track
                ({', '.join(_TRACK_COLS)})
            VALUES ({', '.join('?' for _ in _TRACK_COLS)})
            """,
            [
                tid, submission_id, title.strip(), fields.get("version"),
                track_number, int(fields.get("disc_number", 1)),
                fields.get("primary_artist_id") or sub["artist_profile_id"],
                fields.get("duration_ms"), fields.get("isrc"),
                bool(fields.get("explicit", False)), fields.get("audio_media_id"),
                None, fields.get("rights_contract_id"),
                fields.get("warehouse_track_id"), "pending", sort_order, now, now,
            ],
        )
        row = self._conn.execute(
            f"SELECT {', '.join(_TRACK_COLS)} FROM app_release_submission_track WHERE id = ?",
            [tid],
        ).fetchone()
        return _row_dict(_TRACK_COLS, row)

    def update_track(
        self,
        *,
        submission_id: int,
        track_id: int,
        organization_id: int,
        **fields: Any,
    ) -> dict[str, Any]:
        sub = self._get_submission(submission_id, org_id=organization_id)
        self._assert_editable(sub)
        row = self._conn.execute(
            f"""
            SELECT {', '.join(_TRACK_COLS)} FROM app_release_submission_track
            WHERE id = ? AND submission_id = ?
            """,
            [track_id, submission_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"Track {track_id} not found")
        allowed = {
            "title", "version", "track_number", "disc_number", "primary_artist_id",
            "duration_ms", "isrc", "explicit", "audio_media_id", "rights_contract_id",
            "warehouse_track_id", "validation_status", "sort_order",
        }
        sets: list[str] = []
        params: list[Any] = []
        for k, v in fields.items():
            if k in allowed and v is not None:
                sets.append(f"{k} = ?")
                params.append(v)
        if sets:
            sets.append("updated_at = ?")
            params.append(_now())
            params.extend([track_id, submission_id])
            self._conn.execute(
                f"""
                UPDATE app_release_submission_track SET {', '.join(sets)}
                WHERE id = ? AND submission_id = ?
                """,
                params,
            )
        row = self._conn.execute(
            f"""
            SELECT {', '.join(_TRACK_COLS)} FROM app_release_submission_track
            WHERE id = ? AND submission_id = ?
            """,
            [track_id, submission_id],
        ).fetchone()
        return _row_dict(_TRACK_COLS, row)

    def reorder_tracks(
        self,
        *,
        submission_id: int,
        organization_id: int,
        ordered_track_ids: list[int],
    ) -> list[dict[str, Any]]:
        sub = self._get_submission(submission_id, org_id=organization_id)
        self._assert_editable(sub)
        now = _now()
        for idx, tid in enumerate(ordered_track_ids):
            self._conn.execute(
                """
                UPDATE app_release_submission_track
                SET sort_order = ?, track_number = ?, updated_at = ?
                WHERE id = ? AND submission_id = ?
                """,
                [idx * 10, idx + 1, now, tid, submission_id],
            )
        return self._tracks(submission_id)

    def add_contributor(
        self,
        *,
        submission_id: int,
        organization_id: int,
        party_role: str,
        display_name: str,
        track_id: Optional[int] = None,
        artist_profile_id: Optional[int] = None,
    ) -> dict[str, Any]:
        self._get_submission(submission_id, org_id=organization_id)
        if party_role not in (
            "primary_artist", "featured", "composer", "producer", "label"
        ):
            raise ValidationError(f"Invalid party_role: {party_role}")
        cid = _next_id(self._conn, "app_release_contributor")
        now = _now()
        self._conn.execute(
            """
            INSERT INTO app_release_contributor
                (id, submission_id, track_id, party_role, artist_profile_id,
                 display_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                cid, submission_id, track_id, party_role, artist_profile_id,
                display_name, now,
            ],
        )
        return {
            "id": cid,
            "submission_id": submission_id,
            "track_id": track_id,
            "party_role": party_role,
            "artist_profile_id": artist_profile_id,
            "display_name": display_name,
            "created_at": now,
        }

    # ── media uploads ──────────────────────────────────────────────────────

    def upload_audio(
        self,
        *,
        submission_id: int,
        track_id: int,
        organization_id: int,
        actor_user_id: int,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> dict[str, Any]:
        sub = self._get_submission(submission_id, org_id=organization_id)
        self._assert_editable(sub)
        if ".." in filename.replace("\\", "/") or filename.startswith(("/", "\\")):
            raise MediaValidationError("Path traversal blocked in filename")

        checks = self._media.validate_audio(
            filename=filename, content_type=content_type, data=data
        )
        if any(not c.passed for c in checks):
            detail = "; ".join(c.detail for c in checks if not c.passed)
            raise MediaValidationError(detail or "Audio validation failed")

        stored = self._media.store_private(
            organization_id=organization_id,
            kind="audio",
            filename=filename,
            content_type=content_type,
            data=data,
        )
        # Duplicate hash in org → block
        dup = self._conn.execute(
            """
            SELECT id FROM app_media_asset
            WHERE organization_id = ? AND sha256 = ? AND kind = 'audio'
              AND status != 'deleted'
            LIMIT 1
            """,
            [organization_id, stored.sha256],
        ).fetchone()
        if dup:
            did = _next_id(self._conn, "app_catalog_duplicate_candidate")
            self._conn.execute(
                """
                INSERT INTO app_catalog_duplicate_candidate
                    (id, submission_id, track_id, match_type, matched_ref, severity, created_at)
                VALUES (?, ?, ?, 'hash', ?, 'block', ?)
                """,
                [did, submission_id, track_id, f"media:{dup[0]}", _now()],
            )
            raise ConflictError(
                f"Duplicate audio hash already exists as media {dup[0]}"
            )

        mid = self._persist_media(
            organization_id=organization_id,
            kind="audio",
            content_type=content_type,
            filename=filename,
            stored=stored,
            actor_user_id=actor_user_id,
            checks=checks,
        )
        self.update_track(
            submission_id=submission_id,
            track_id=track_id,
            organization_id=organization_id,
            audio_media_id=mid,
            duration_ms=stored.duration_ms,
            validation_status="ok",
        )
        return self._get_media(mid)

    def upload_cover(
        self,
        *,
        submission_id: int,
        organization_id: int,
        actor_user_id: int,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> dict[str, Any]:
        sub = self._get_submission(submission_id, org_id=organization_id)
        self._assert_editable(sub)
        if ".." in filename.replace("\\", "/") or filename.startswith(("/", "\\")):
            raise MediaValidationError("Path traversal blocked in filename")

        checks = self._media.validate_image(
            filename=filename, content_type=content_type, data=data
        )
        if any(not c.passed for c in checks):
            detail = "; ".join(c.detail for c in checks if not c.passed)
            raise MediaValidationError(detail or "Image validation failed")

        stored = self._media.store_private(
            organization_id=organization_id,
            kind="cover",
            filename=filename,
            content_type=content_type,
            data=data,
        )
        mid = self._persist_media(
            organization_id=organization_id,
            kind="cover",
            content_type=content_type,
            filename=filename,
            stored=stored,
            actor_user_id=actor_user_id,
            checks=checks,
        )
        self.update_metadata(
            submission_id=submission_id,
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            cover_media_id=mid,
        )
        return self._get_media(mid)

    def _persist_media(
        self,
        *,
        organization_id: int,
        kind: str,
        content_type: str,
        filename: str,
        stored: Any,
        actor_user_id: int,
        checks: list,
    ) -> int:
        now = _now()
        mid = _next_id(self._conn, "app_media_asset")
        self._conn.execute(
            f"""
            INSERT INTO app_media_asset
                ({', '.join(_MEDIA_COLS)})
            VALUES ({', '.join('?' for _ in _MEDIA_COLS)})
            """,
            [
                mid, organization_id, kind, content_type, filename,
                stored.stored_name, stored.relative_path, stored.byte_size,
                stored.sha256, stored.duration_ms, stored.width, stored.height,
                "private", actor_user_id, now,
            ],
        )
        uid = _next_id(self._conn, "app_media_upload")
        self._conn.execute(
            """
            INSERT INTO app_media_upload
                (id, media_asset_id, upload_status, rejection_reason, created_at)
            VALUES (?, ?, 'validated', NULL, ?)
            """,
            [uid, mid, now],
        )
        for c in checks:
            vid = _next_id(self._conn, "app_media_validation")
            self._conn.execute(
                """
                INSERT INTO app_media_validation
                    (id, media_asset_id, check_code, passed, detail, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [vid, mid, c.check_code, c.passed, c.detail, now],
            )
        return mid

    # ── validation / duplicates / rights ───────────────────────────────────

    def _detect_duplicates(self, sub: dict[str, Any]) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        org_id = int(sub["organization_id"])
        sid = int(sub["id"])
        for tr in self._tracks(sid):
            if tr.get("isrc"):
                other = self._conn.execute(
                    """
                    SELECT t.id FROM app_release_submission_track t
                    JOIN app_release_submission s ON s.id = t.submission_id
                    WHERE s.organization_id = ? AND t.isrc = ? AND t.id != ?
                      AND s.status NOT IN ('withdrawn', 'archived', 'rejected')
                    LIMIT 1
                    """,
                    [org_id, tr["isrc"], tr["id"]],
                ).fetchone()
                if other:
                    issues.append(
                        {
                            "severity": "block",
                            "code": "duplicate_isrc",
                            "message": f"ISRC {tr['isrc']} already used",
                            "field_ref": f"track.{tr['id']}.isrc",
                            "track_id": tr["id"],
                            "match_type": "isrc",
                            "matched_ref": f"track:{other[0]}",
                        }
                    )
            # Soft warn: title + primary artist + duration
            if tr.get("title") and tr.get("duration_ms"):
                soft = self._conn.execute(
                    """
                    SELECT t.id FROM app_release_submission_track t
                    JOIN app_release_submission s ON s.id = t.submission_id
                    WHERE s.organization_id = ?
                      AND LOWER(t.title) = LOWER(?)
                      AND t.duration_ms = ?
                      AND COALESCE(t.primary_artist_id, -1) = COALESCE(?, -1)
                      AND t.id != ?
                      AND s.status NOT IN ('withdrawn', 'archived', 'rejected')
                    LIMIT 1
                    """,
                    [
                        org_id,
                        tr["title"],
                        tr["duration_ms"],
                        tr.get("primary_artist_id"),
                        tr["id"],
                    ],
                ).fetchone()
                if soft:
                    issues.append(
                        {
                            "severity": "warn",
                            "code": "soft_duplicate_title_artist_duration",
                            "message": "Similar title/artist/duration found",
                            "field_ref": f"track.{tr['id']}",
                            "track_id": tr["id"],
                            "match_type": "title_artist_duration",
                            "matched_ref": f"track:{soft[0]}",
                        }
                    )
        for iss in issues:
            did = _next_id(self._conn, "app_catalog_duplicate_candidate")
            self._conn.execute(
                """
                INSERT INTO app_catalog_duplicate_candidate
                    (id, submission_id, track_id, match_type, matched_ref, severity, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    did, sid, iss.get("track_id"), iss["match_type"],
                    iss["matched_ref"], iss["severity"], _now(),
                ],
            )
            self._add_issue(
                submission_id=sid,
                severity=iss["severity"],
                code=iss["code"],
                message=iss["message"],
                field_ref=iss.get("field_ref"),
            )
        return issues

    def check_rights_gate(
        self,
        sub: dict[str, Any],
        *,
        strict_block: bool = True,
    ) -> list[dict[str, Any]]:
        """Validate ownership sum == 100, period, conflict; return issues."""
        issues: list[dict[str, Any]] = []
        sid = int(sub["id"])
        contract_id = sub.get("rights_contract_id")
        asset_id = sub.get("catalog_asset_id")

        # Prefer track-level contract if set
        tracks = self._tracks(sid)
        for tr in tracks:
            if tr.get("rights_contract_id"):
                contract_id = tr["rights_contract_id"]
            if tr.get("catalog_asset_id"):
                asset_id = tr["catalog_asset_id"]

        if not contract_id:
            issues.append(
                {
                    "severity": "block",
                    "code": "missing_rights_contract",
                    "message": "rights_contract_id is required for approve/publish",
                }
            )
            return issues

        if not _table_exists(self._conn, "app_rights_contract"):
            if sub.get("is_demo"):
                issues.append(
                    {
                        "severity": "warn",
                        "code": "rights_tables_missing",
                        "message": "Rights tables missing; demo allowed with WARN",
                    }
                )
                return issues
            issues.append(
                {
                    "severity": "block",
                    "code": "rights_tables_missing",
                    "message": "Rights tables missing",
                }
            )
            return issues

        crow = self._conn.execute(
            """
            SELECT id, asset_id, rights_type, status, valid_from, valid_to
            FROM app_rights_contract WHERE id = ?
            """,
            [contract_id],
        ).fetchone()
        if not crow:
            issues.append(
                {
                    "severity": "block",
                    "code": "contract_not_found",
                    "message": f"Contract {contract_id} not found",
                }
            )
            return issues

        parties = self._conn.execute(
            """
            SELECT ownership_percentage FROM app_rights_contract_party
            WHERE contract_id = ?
            """,
            [contract_id],
        ).fetchall()
        total = sum((_dec(p[0]) for p in parties), ZERO)
        if total != HUNDRED:
            issues.append(
                {
                    "severity": "block",
                    "code": "ownership_sum",
                    "message": f"Ownership sum is {total}, required 100",
                }
            )

        target_date = sub.get("actual_release_date") or sub.get("planned_release_date")
        if target_date is not None:
            vf, vt = crow[4], crow[5]
            if vf and target_date < vf:
                issues.append(
                    {
                        "severity": "block",
                        "code": "rights_period",
                        "message": "Release date before contract valid_from",
                    }
                )
            if vt and target_date > vt:
                issues.append(
                    {
                        "severity": "block",
                        "code": "rights_period",
                        "message": "Release date after contract valid_to",
                    }
                )

        # Territory / authorized_use — warn if empty for demo, else soft
        terr = self._conn.execute(
            "SELECT COUNT(*) FROM app_rights_territory WHERE contract_id = ?",
            [contract_id],
        ).fetchone()
        ause = self._conn.execute(
            """
            SELECT COUNT(*) FROM app_rights_authorized_use
            WHERE contract_id = ? AND LOWER(use_code) LIKE '%stream%'
            """,
            [contract_id],
        ).fetchone()
        if (not terr or terr[0] == 0) or (not ause or ause[0] == 0):
            issues.append(
                {
                    "severity": "warn",
                    "code": "missing_territory_or_streaming_use",
                    "message": "Territory or streaming authorized_use missing",
                }
            )

        check_asset = asset_id or crow[1]
        if check_asset and _table_exists(self._conn, "app_rights_conflict"):
            open_c = self._conn.execute(
                """
                SELECT id FROM app_rights_conflict
                WHERE asset_id = ? AND status = 'open' LIMIT 1
                """,
                [check_asset],
            ).fetchone()
            if open_c:
                issues.append(
                    {
                        "severity": "block",
                        "code": "open_rights_conflict",
                        "message": f"Open conflict {open_c[0]} on asset {check_asset}",
                    }
                )

        for iss in issues:
            self._add_issue(
                submission_id=sid,
                severity=iss["severity"],
                code=iss["code"],
                message=iss["message"],
            )

        if strict_block and any(i["severity"] == "block" for i in issues):
            raise RightsGateError(
                "; ".join(i["message"] for i in issues if i["severity"] == "block")
            )
        return issues

    def validate_ready(
        self, *, submission_id: int, organization_id: int
    ) -> dict[str, Any]:
        sub = self._get_submission(submission_id, org_id=organization_id)
        tracks = self._tracks(submission_id)
        blockers: list[str] = []
        if not tracks:
            blockers.append("no_tracks")
        for tr in tracks:
            if not tr.get("audio_media_id"):
                blockers.append(f"track_{tr['id']}_missing_audio")
                self._conn.execute(
                    """
                    UPDATE app_release_submission_track
                    SET validation_status = 'missing_audio', updated_at = ?
                    WHERE id = ?
                    """,
                    [_now(), tr["id"]],
                )
        if not sub.get("cover_media_id"):
            blockers.append("missing_cover")
        dups = self._detect_duplicates(sub)
        if any(d["severity"] == "block" for d in dups):
            blockers.append("duplicate_block")
        return {
            "submission_id": submission_id,
            "ready": len(blockers) == 0,
            "blockers": blockers,
            "duplicates": dups,
            "track_count": len(tracks),
        }

    # ── workflow actions ───────────────────────────────────────────────────

    def submit(
        self, *, submission_id: int, organization_id: int, actor_user_id: int
    ) -> dict[str, Any]:
        sub = self._get_submission(submission_id, org_id=organization_id)
        ready = self.validate_ready(
            submission_id=submission_id, organization_id=organization_id
        )
        if not ready["ready"]:
            raise ValidationError(
                f"Submission not ready: {', '.join(ready['blockers'])}"
            )
        if sub["status"] == "draft":
            sub = transition(
                self._conn, sub, "submitted", actor_user_id=actor_user_id, reason="submit"
            )
        elif sub["status"] == "changes_requested":
            sub = transition(
                self._conn, sub, "submitted", actor_user_id=actor_user_id, reason="resubmit"
            )
        else:
            raise InvalidTransitionError(f"Cannot submit from {sub['status']}")
        # Auto move to under_review for queue visibility
        try:
            sub = transition(
                self._conn,
                sub,
                "under_review",
                actor_user_id=actor_user_id,
                reason="auto_queue",
            )
        except Exception:
            # If self-approve guard blocks under_review from same actor, stay submitted
            pass
        return self._get_submission(submission_id)

    def request_changes(
        self,
        *,
        submission_id: int,
        organization_id: int,
        actor_user_id: int,
        notes: str,
    ) -> dict[str, Any]:
        sub = self._get_submission(submission_id, org_id=organization_id)
        if sub["status"] not in ("submitted", "under_review"):
            # Allow from submitted via under_review first
            if sub["status"] == "submitted":
                sub = transition(
                    self._conn,
                    sub,
                    "under_review",
                    actor_user_id=actor_user_id,
                    reason="review_start",
                )
        sub = transition(
            self._conn,
            sub,
            "changes_requested",
            actor_user_id=actor_user_id,
            reason=notes,
        )
        rid = _next_id(self._conn, "app_release_review")
        self._conn.execute(
            """
            INSERT INTO app_release_review
                (id, submission_id, reviewer_id, decision, notes, created_at)
            VALUES (?, ?, ?, 'changes_requested', ?, ?)
            """,
            [rid, submission_id, actor_user_id, notes, _now()],
        )
        self._conn.execute(
            "UPDATE app_release_submission SET reviewer_id = ?, updated_at = ? WHERE id = ?",
            [actor_user_id, _now(), submission_id],
        )
        return self._get_submission(submission_id)

    def approve(
        self,
        *,
        submission_id: int,
        organization_id: int,
        actor_user_id: int,
        notes: Optional[str] = None,
    ) -> dict[str, Any]:
        sub = self._get_submission(submission_id, org_id=organization_id)
        self.check_rights_gate(sub, strict_block=True)
        if sub["status"] == "submitted":
            sub = transition(
                self._conn,
                sub,
                "under_review",
                actor_user_id=actor_user_id,
                reason="review_start",
            )
        sub = transition(
            self._conn,
            sub,
            "approved",
            actor_user_id=actor_user_id,
            reason=notes or "approved",
        )
        rid = _next_id(self._conn, "app_release_review")
        self._conn.execute(
            """
            INSERT INTO app_release_review
                (id, submission_id, reviewer_id, decision, notes, created_at)
            VALUES (?, ?, ?, 'approve', ?, ?)
            """,
            [rid, submission_id, actor_user_id, notes, _now()],
        )
        self._conn.execute(
            "UPDATE app_release_submission SET reviewer_id = ?, updated_at = ? WHERE id = ?",
            [actor_user_id, _now(), submission_id],
        )
        return self._get_submission(submission_id)

    def reject(
        self,
        *,
        submission_id: int,
        organization_id: int,
        actor_user_id: int,
        reason: str,
    ) -> dict[str, Any]:
        sub = self._get_submission(submission_id, org_id=organization_id)
        if sub["status"] == "submitted":
            sub = transition(
                self._conn,
                sub,
                "under_review",
                actor_user_id=actor_user_id,
                reason="review_start",
            )
        sub = transition(
            self._conn, sub, "rejected", actor_user_id=actor_user_id, reason=reason
        )
        self._conn.execute(
            """
            UPDATE app_release_submission
            SET reject_reason = ?, reviewer_id = ?, updated_at = ?
            WHERE id = ?
            """,
            [reason, actor_user_id, _now(), submission_id],
        )
        rid = _next_id(self._conn, "app_release_review")
        self._conn.execute(
            """
            INSERT INTO app_release_review
                (id, submission_id, reviewer_id, decision, notes, created_at)
            VALUES (?, ?, ?, 'reject', ?, ?)
            """,
            [rid, submission_id, actor_user_id, reason, _now()],
        )
        return self._get_submission(submission_id)

    def schedule(
        self,
        *,
        submission_id: int,
        organization_id: int,
        actor_user_id: int,
        scheduled_at: Optional[datetime] = None,
    ) -> dict[str, Any]:
        sub = self._get_submission(submission_id, org_id=organization_id)
        if sub["status"] != "approved":
            raise InvalidTransitionError("schedule requires approved status")
        when = scheduled_at or _now()
        self._conn.execute(
            "UPDATE app_release_submission SET scheduled_at = ?, updated_at = ? WHERE id = ?",
            [when, _now(), submission_id],
        )
        sub = self._get_submission(submission_id)
        return transition(
            self._conn, sub, "scheduled", actor_user_id=actor_user_id, reason="schedule"
        )

    def publish(
        self,
        *,
        submission_id: int,
        organization_id: int,
        actor_user_id: int,
        idempotency_key: Optional[str] = None,
    ) -> dict[str, Any]:
        sub = self._get_submission(submission_id, org_id=organization_id)
        key = idempotency_key or f"publish-{submission_id}"
        existing = self._conn.execute(
            "SELECT id, submission_id FROM app_release_publication WHERE idempotency_key = ?",
            [key],
        ).fetchone()
        if existing:
            if int(existing[1]) != int(submission_id):
                raise IdempotencyConflictError("Idempotency key used by another submission")
            return {
                "submission": self._get_submission(submission_id),
                "publication_id": int(existing[0]),
                "idempotent": True,
            }

        if sub["status"] not in ("approved", "scheduled"):
            raise InvalidTransitionError(
                f"publish requires approved/scheduled, got {sub['status']}"
            )

        self.check_rights_gate(sub, strict_block=True)
        tracks = self._tracks(submission_id)
        if not tracks:
            raise ValidationError("No tracks to publish")

        warehouse_ids: list[int] = []
        primary_asset_id = sub.get("catalog_asset_id")

        for tr in tracks:
            wtid = self._ensure_warehouse_track(tr, sub)
            warehouse_ids.append(wtid)
            asset_id = self._ensure_catalog_asset(tr, sub, wtid, actor_user_id)
            if primary_asset_id is None:
                primary_asset_id = asset_id
            self._conn.execute(
                """
                UPDATE app_release_submission_track
                SET warehouse_track_id = ?, catalog_asset_id = ?, updated_at = ?
                WHERE id = ?
                """,
                [wtid, asset_id, _now(), tr["id"]],
            )
            playable = f"/api/v1/media/{tr['audio_media_id']}/content"
            self._upsert_audio_source(wtid, playable)
            if sub.get("cover_media_id"):
                self._upsert_cover(wtid, int(sub["cover_media_id"]))
            # Promote audio media status
            if tr.get("audio_media_id"):
                self._conn.execute(
                    "UPDATE app_media_asset SET status = 'published' WHERE id = ?",
                    [tr["audio_media_id"]],
                )

        if sub.get("cover_media_id"):
            self._conn.execute(
                "UPDATE app_media_asset SET status = 'published' WHERE id = ?",
                [sub["cover_media_id"]],
            )

        self._conn.execute(
            """
            UPDATE app_release_submission
            SET catalog_asset_id = ?, updated_at = ?
            WHERE id = ?
            """,
            [primary_asset_id, _now(), submission_id],
        )
        sub = self._get_submission(submission_id)
        sub = transition(
            self._conn, sub, "published", actor_user_id=actor_user_id, reason="publish"
        )

        pub_id = _next_id(self._conn, "app_release_publication")
        self._conn.execute(
            """
            INSERT INTO app_release_publication
                (id, submission_id, published_by, published_at, version_label,
                 warehouse_track_ids_json, idempotency_key)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                pub_id,
                submission_id,
                actor_user_id,
                _now(),
                "v1",
                json.dumps(warehouse_ids),
                key,
            ],
        )
        self._record_event(
            submission_id,
            "published",
            actor_user_id,
            {"warehouse_track_ids": warehouse_ids, "publication_id": pub_id},
        )
        return {
            "submission": self._get_submission(submission_id),
            "publication_id": pub_id,
            "warehouse_track_ids": warehouse_ids,
            "idempotent": False,
        }

    def _ensure_warehouse_track(
        self, track: dict[str, Any], sub: dict[str, Any]
    ) -> int:
        if track.get("warehouse_track_id"):
            wtid = int(track["warehouse_track_id"])
            if wtid < 100000 and not sub.get("is_demo"):
                # Reuse existing imported track for linking — do not mutate it.
                return wtid
            if wtid >= DEMO_WAREHOUSE_TRACK_ID_MIN:
                self._upsert_public_dim_track(wtid, track, sub)
                return wtid
            if wtid < 100000:
                return wtid

        if not _table_exists(self._conn, "dim_track"):
            # App-only: allocate reserved id even without warehouse physical insert
            nxt = self._conn.execute(
                """
                SELECT COALESCE(MAX(warehouse_track_id), ?) + 1
                FROM app_release_submission_track
                WHERE warehouse_track_id >= ?
                """,
                [DEMO_WAREHOUSE_TRACK_ID_MIN - 1, DEMO_WAREHOUSE_TRACK_ID_MIN],
            ).fetchone()
            return max(int(nxt[0]), DEMO_WAREHOUSE_TRACK_ID_MIN)

        nxt_row = self._conn.execute(
            "SELECT COALESCE(MAX(id_track), ?) + 1 FROM dim_track WHERE id_track >= ?",
            [DEMO_WAREHOUSE_TRACK_ID_MIN - 1, DEMO_WAREHOUSE_TRACK_ID_MIN],
        ).fetchone()
        wtid = max(int(nxt_row[0]), DEMO_WAREHOUSE_TRACK_ID_MIN)
        self._upsert_public_dim_track(wtid, track, sub)
        return wtid

    def _public_catalog_title(self, track: dict[str, Any], sub: dict[str, Any]) -> str:
        track_title = (track.get("title") or "").strip()
        release_title = (sub.get("title") or "").strip()
        tl = track_title.lower()
        placeholder = (
            not track_title
            or tl in ("track", "untitled", "song", "published track")
            or tl.endswith(" track")
        )
        # Prefer intentional release title (e.g. "[DEMO] Published Single").
        if release_title and (placeholder or release_title.upper().startswith("[DEMO")):
            chosen = release_title
        else:
            chosen = track_title or release_title or "Untitled"
        if (
            sub.get("is_demo")
            and DEMO_TRACK_TITLE_PREFIX not in chosen
            and not chosen.upper().startswith("[DEMO")
        ):
            chosen = f"{DEMO_TRACK_TITLE_PREFIX} {chosen}"
        return chosen

    def _ensure_warehouse_artist_id(self, sub: dict[str, Any]) -> Optional[int]:
        """Resolve / create dim_artista for the submission artist profile."""
        if not _table_exists(self._conn, "dim_artista"):
            return None
        profile_id = sub.get("artist_profile_id")
        display = "Demo Artist"
        warehouse_artist_id = None
        if profile_id and _table_exists(self._conn, "app_artist_profile"):
            prow = self._conn.execute(
                """
                SELECT display_name, warehouse_artist_id
                FROM app_artist_profile WHERE id = ?
                """,
                [int(profile_id)],
            ).fetchone()
            if prow:
                display = (prow[0] or display).strip() or display
                if prow[1] is not None:
                    warehouse_artist_id = int(prow[1])

        if warehouse_artist_id is not None:
            exists = self._conn.execute(
                "SELECT 1 FROM dim_artista WHERE id_artista = ?",
                [warehouse_artist_id],
            ).fetchone()
            if exists:
                return warehouse_artist_id

        by_name = self._conn.execute(
            """
            SELECT id_artista FROM dim_artista
            WHERE lower(trim(nombre_artista)) = lower(trim(?))
            LIMIT 1
            """,
            [display],
        ).fetchone()
        if by_name:
            aid = int(by_name[0])
        else:
            # Reserved artist ids for published demo profiles (avoid colliding with imports)
            nxt = self._conn.execute(
                "SELECT COALESCE(MAX(id_artista), 9000000) + 1 FROM dim_artista WHERE id_artista >= 9000000"
            ).fetchone()
            aid = max(int(nxt[0]), 9_000_000)
            self._conn.execute(
                "INSERT INTO dim_artista (id_artista, nombre_artista) VALUES (?, ?)",
                [aid, display],
            )

        if profile_id and _table_exists(self._conn, "app_artist_profile"):
            self._conn.execute(
                """
                UPDATE app_artist_profile
                SET warehouse_artist_id = ?, updated_at = ?
                WHERE id = ? AND (warehouse_artist_id IS NULL OR warehouse_artist_id = 0)
                """,
                [aid, _now(), int(profile_id)],
            )
        return aid

    def _upsert_public_dim_track(
        self, wtid: int, track: dict[str, Any], sub: dict[str, Any]
    ) -> None:
        """Create or refresh the discoverable dim_track row for a published track."""
        if not _table_exists(self._conn, "dim_track"):
            return
        title = self._public_catalog_title(track, sub)
        artist_id = self._ensure_warehouse_artist_id(sub)
        duration = int(track.get("duration_ms") or 0)
        cols = {
            r[0]
            for r in self._conn.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'dim_track'"
            ).fetchall()
        }
        existing = self._conn.execute(
            "SELECT 1 FROM dim_track WHERE id_track = ?", [wtid]
        ).fetchone()
        if existing:
            # DuckDB ART indexes can raise duplicate-key on UPDATE; replace row.
            self._conn.execute("DELETE FROM dim_track WHERE id_track = ?", [wtid])

        fields = ["id_track", "nombre_track"]
        values: list[Any] = [wtid, title]
        if "duration_ms" in cols:
            fields.append("duration_ms")
            values.append(duration)
        if "popularity" in cols:
            fields.append("popularity")
            values.append(90)
        if "id_artista" in cols and artist_id is not None:
            fields.append("id_artista")
            values.append(artist_id)

        # Build search_fold before insert so discoverability is immediate.
        if "search_fold" in cols:
            from app.core.search_fold import _row_search_fold
            from app.packages.catalog.services.text_search import fold_text

            artist_name = None
            if artist_id is not None and _table_exists(self._conn, "dim_artista"):
                arow = self._conn.execute(
                    "SELECT nombre_artista FROM dim_artista WHERE id_artista = ?",
                    [artist_id],
                ).fetchone()
                if arow:
                    artist_name = arow[0]
            release_title = (sub.get("title") or "").strip()
            folded = _row_search_fold(title, artist_name, None)
            if release_title:
                rt = fold_text(release_title)
                if rt and rt not in folded:
                    folded = f"{folded} {rt}".strip()
            fields.append("search_fold")
            values.append(folded)

        placeholders = ", ".join("?" for _ in fields)
        self._conn.execute(
            f"INSERT INTO dim_track ({', '.join(fields)}) VALUES ({placeholders})",
            values,
        )

    def _ensure_catalog_asset(
        self,
        track: dict[str, Any],
        sub: dict[str, Any],
        warehouse_track_id: int,
        actor_user_id: int,
    ) -> int:
        if track.get("catalog_asset_id"):
            return int(track["catalog_asset_id"])
        if not _table_exists(self._conn, "app_catalog_asset"):
            return 0
        now = _now()
        aid = _next_id(self._conn, "app_catalog_asset")
        self._conn.execute(
            """
            INSERT INTO app_catalog_asset
                (id, organization_id, title, status, warehouse_track_id,
                 artist_profile_id, created_by, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, ?, ?, ?, ?)
            """,
            [
                aid,
                sub["organization_id"],
                track["title"],
                warehouse_track_id,
                sub["artist_profile_id"],
                actor_user_id,
                now,
                now,
            ],
        )
        return aid

    def _upsert_audio_source(self, warehouse_track_id: int, playable_url: str) -> None:
        if not _table_exists(self._conn, "app_track_audio_source"):
            return
        from app.packages.streaming.services.audio.cache import migrate_audio_source_columns

        migrate_audio_source_columns(self._conn)
        self._conn.execute(
            "DELETE FROM app_track_audio_source WHERE track_id = ?",
            [warehouse_track_id],
        )
        self._conn.execute(
            """
            INSERT INTO app_track_audio_source
                (track_id, provider, youtube_video_id, source_ref, playable_url,
                 query, status, failure_count, confidence_score, resolved_at, last_checked_at)
            VALUES (?, 'local_published', NULL, ?, ?, 'local_published', 'ok', 0, 1.0, ?, ?)
            """,
            [
                warehouse_track_id,
                str(warehouse_track_id),
                playable_url,
                _now(),
                _now(),
            ],
        )

    def _upsert_cover(self, warehouse_track_id: int, cover_media_id: int) -> None:
        if not _table_exists(self._conn, "app_track_cover"):
            return
        url = f"/api/v1/media/{cover_media_id}/content"
        self._conn.execute(
            "DELETE FROM app_track_cover WHERE track_id = ?", [warehouse_track_id]
        )
        self._conn.execute(
            """
            INSERT INTO app_track_cover (track_id, image_url, status, resolved_at)
            VALUES (?, ?, 'ok', ?)
            """,
            [warehouse_track_id, url, _now()],
        )

    def suspend(
        self,
        *,
        submission_id: int,
        organization_id: int,
        actor_user_id: int,
        reason: str,
    ) -> dict[str, Any]:
        sub = self._get_submission(submission_id, org_id=organization_id)
        sub = transition(
            self._conn, sub, "suspended", actor_user_id=actor_user_id, reason=reason
        )
        tid = _next_id(self._conn, "app_release_takedown")
        self._conn.execute(
            """
            INSERT INTO app_release_takedown
                (id, submission_id, reason, actor_user_id, kind, created_at)
            VALUES (?, ?, ?, ?, 'suspend', ?)
            """,
            [tid, submission_id, reason, actor_user_id, _now()],
        )
        # Mark audio sources disabled so playback is blocked
        for tr in self._tracks(submission_id):
            if tr.get("warehouse_track_id") and _table_exists(
                self._conn, "app_track_audio_source"
            ):
                self._conn.execute(
                    """
                    UPDATE app_track_audio_source SET status = 'disabled'
                    WHERE track_id = ? AND provider = 'local_published'
                    """,
                    [tr["warehouse_track_id"]],
                )
        self._record_event(submission_id, "suspended", actor_user_id, {"reason": reason})
        return self._get_submission(submission_id)

    def withdraw(
        self,
        *,
        submission_id: int,
        organization_id: int,
        actor_user_id: int,
        reason: str,
    ) -> dict[str, Any]:
        sub = self._get_submission(submission_id, org_id=organization_id)
        sub = transition(
            self._conn, sub, "withdrawn", actor_user_id=actor_user_id, reason=reason
        )
        tid = _next_id(self._conn, "app_release_takedown")
        self._conn.execute(
            """
            INSERT INTO app_release_takedown
                (id, submission_id, reason, actor_user_id, kind, created_at)
            VALUES (?, ?, ?, ?, 'withdraw', ?)
            """,
            [tid, submission_id, reason, actor_user_id, _now()],
        )
        self._conn.execute(
            """
            UPDATE app_release_submission
            SET withdraw_reason = ?, updated_at = ? WHERE id = ?
            """,
            [reason, _now(), submission_id],
        )
        for tr in self._tracks(submission_id):
            if tr.get("warehouse_track_id") and _table_exists(
                self._conn, "app_track_audio_source"
            ):
                self._conn.execute(
                    """
                    UPDATE app_track_audio_source SET status = 'disabled'
                    WHERE track_id = ? AND provider = 'local_published'
                    """,
                    [tr["warehouse_track_id"]],
                )
        self._record_event(submission_id, "withdrawn", actor_user_id, {"reason": reason})
        return self._get_submission(submission_id)

    # ── reads ──────────────────────────────────────────────────────────────

    def list_for_artist(
        self,
        *,
        organization_id: int,
        artist_profile_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        sql = f"""
            SELECT {', '.join(_SUB_COLS)} FROM app_release_submission
            WHERE organization_id = ?
        """
        params: list[Any] = [organization_id]
        if artist_profile_id is not None:
            sql += " AND artist_profile_id = ?"
            params.append(artist_profile_id)
        sql += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        return [_row_dict(_SUB_COLS, r) for r in self._conn.execute(sql, params).fetchall()]

    def list_for_review(
        self,
        *,
        organization_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            f"""
            SELECT {', '.join(_SUB_COLS)} FROM app_release_submission
            WHERE organization_id = ?
              AND status IN ('submitted', 'under_review', 'changes_requested', 'approved', 'scheduled')
            ORDER BY updated_at DESC LIMIT ? OFFSET ?
            """,
            [organization_id, limit, offset],
        ).fetchall()
        return [_row_dict(_SUB_COLS, r) for r in rows]

    def get_detail(
        self, *, submission_id: int, organization_id: int
    ) -> dict[str, Any]:
        sub = self._get_submission(submission_id, org_id=organization_id)
        tracks = self._tracks(submission_id)
        contribs = self._conn.execute(
            """
            SELECT id, submission_id, track_id, party_role, artist_profile_id,
                   display_name, created_at
            FROM app_release_contributor WHERE submission_id = ?
            """,
            [submission_id],
        ).fetchall()
        issues = self._conn.execute(
            """
            SELECT id, severity, code, message, field_ref, resolved, created_at
            FROM app_release_review_issue WHERE submission_id = ?
            ORDER BY id
            """,
            [submission_id],
        ).fetchall()
        return {
            "submission": sub,
            "tracks": tracks,
            "contributors": [
                {
                    "id": c[0],
                    "submission_id": c[1],
                    "track_id": c[2],
                    "party_role": c[3],
                    "artist_profile_id": c[4],
                    "display_name": c[5],
                    "created_at": c[6],
                }
                for c in contribs
            ],
            "issues": [
                {
                    "id": i[0],
                    "severity": i[1],
                    "code": i[2],
                    "message": i[3],
                    "field_ref": i[4],
                    "resolved": i[5],
                    "created_at": i[6],
                }
                for i in issues
            ],
        }

    def history(
        self, *, submission_id: int, organization_id: int
    ) -> list[dict[str, Any]]:
        self._get_submission(submission_id, org_id=organization_id)
        rows = self._conn.execute(
            """
            SELECT id, submission_id, from_status, to_status, actor_user_id, reason, created_at
            FROM app_release_status_history
            WHERE submission_id = ?
            ORDER BY id
            """,
            [submission_id],
        ).fetchall()
        return [
            {
                "id": r[0],
                "submission_id": r[1],
                "from_status": r[2],
                "to_status": r[3],
                "actor_user_id": r[4],
                "reason": r[5],
                "created_at": r[6],
            }
            for r in rows
        ]

    def portal_summary(
        self, *, organization_id: int, user_id: int
    ) -> dict[str, Any]:
        access = self._conn.execute(
            """
            SELECT artist_profile_id FROM app_artist_portal_access
            WHERE user_id = ? AND organization_id = ? AND status = 'active'
            """,
            [user_id, organization_id],
        ).fetchall()
        artist_ids = [int(a[0]) for a in access]
        counts = self._conn.execute(
            """
            SELECT status, COUNT(*) FROM app_release_submission
            WHERE organization_id = ?
              AND (? = 0 OR artist_profile_id IN (
                    SELECT artist_profile_id FROM app_artist_portal_access
                    WHERE user_id = ? AND organization_id = ? AND status = 'active'
                  ))
            GROUP BY status
            """,
            [
                organization_id,
                0 if not artist_ids else 1,
                user_id,
                organization_id,
            ],
        ).fetchall()
        return {
            "organization_id": organization_id,
            "artist_profile_ids": artist_ids,
            "status_counts": {str(r[0]): int(r[1]) for r in counts},
        }

    def get_media_for_serve(
        self, media_id: int, *, user_id: int, organization_id: Optional[int] = None
    ) -> tuple[dict[str, Any], Any]:
        media = self._get_media(media_id)
        status = media["status"]
        if status == "deleted":
            raise NotFoundError("Media deleted")
        if status == "private":
            # Creator, same org member, or reviewer of linked submission
            if int(media["created_by"]) != int(user_id):
                if organization_id is None or int(media["organization_id"]) != int(
                    organization_id
                ):
                    raise NotFoundError("Media not accessible")
        # published: any authenticated caller may play
        path = self._media.resolve_absolute(media["relative_path"])
        if not path.is_file():
            raise NotFoundError("Media file missing on disk")
        return media, path
