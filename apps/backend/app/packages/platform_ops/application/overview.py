"""Platform Ops overview — Spec 055 (read-only queue composition)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal, Optional

import duckdb

from app.core.database import table_exists
from app.packages.catalog_publishing.application.platform_reviews import REVIEWABLE_STATUSES
from app.packages.organizations.domain.enums import ARTIST_WORKSPACE_TYPE

QueueCode = Literal[
    "artist_requests",
    "catalog_reviews",
    "audio_unresolved",
    "incidents",
]
Availability = Literal["available", "unavailable"]
Severity = Literal["normal", "attention", "critical"]
Health = Literal["healthy", "degraded", "unavailable"]

QUEUE_PRIORITY: tuple[QueueCode, ...] = (
    "artist_requests",
    "catalog_reviews",
    "audio_unresolved",
    "incidents",
)


@dataclass(frozen=True)
class QueueSnapshot:
    code: QueueCode
    count: Optional[int]
    availability: Availability
    severity: Severity


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_count(conn: duckdb.DuckDBPyConnection, sql: str, params: list[Any] | None = None) -> Optional[int]:
    try:
        row = conn.execute(sql, params or []).fetchone()
        if row is None or row[0] is None:
            return 0
        return int(row[0])
    except Exception:
        return None


def _count_artist_requests(conn: duckdb.DuckDBPyConnection) -> Optional[int]:
    if not table_exists(conn, "app_artist_access_request"):
        return None
    return _safe_count(
        conn,
        """
        SELECT COUNT(*) FROM app_artist_access_request
        WHERE request_type IN ('claim_ownership', 'create_new')
          AND status = 'pending'
        """,
    )


def _count_catalog_reviews(conn: duckdb.DuckDBPyConnection) -> Optional[int]:
    if not table_exists(conn, "app_release_submission") or not table_exists(
        conn, "app_organization"
    ):
        return None
    placeholders = ", ".join("?" for _ in REVIEWABLE_STATUSES)
    return _safe_count(
        conn,
        f"""
        SELECT COUNT(*)
        FROM app_release_submission s
        INNER JOIN app_organization o ON o.id = s.organization_id
        WHERE o.organization_type = ?
          AND s.status IN ({placeholders})
        """,
        [ARTIST_WORKSPACE_TYPE, *REVIEWABLE_STATUSES],
    )


def _count_audio_unresolved(conn: duckdb.DuckDBPyConnection) -> Optional[int]:
    if not table_exists(conn, "app_track_audio_source"):
        return None
    return _safe_count(
        conn,
        """
        SELECT COUNT(*) FROM app_track_audio_source
        WHERE status IN ('not_found', 'error', 'disabled')
          AND COALESCE(provider, '') <> 'local_published'
        """,
    )


def _count_incidents(conn: duckdb.DuckDBPyConnection) -> Optional[int]:
    if not table_exists(conn, "app_operational_incident"):
        return None
    return _safe_count(
        conn,
        """
        SELECT COUNT(*) FROM app_operational_incident
        WHERE status IN ('open', 'investigating')
        """,
    )


def _severity(code: QueueCode, count: Optional[int], availability: Availability) -> Severity:
    if availability == "unavailable" or count is None or count <= 0:
        return "normal"
    if code == "incidents":
        return "critical"
    return "attention"


def _build_queue(
    code: QueueCode, count: Optional[int]
) -> QueueSnapshot:
    availability: Availability = "unavailable" if count is None else "available"
    return QueueSnapshot(
        code=code,
        count=count,
        availability=availability,
        severity=_severity(code, count, availability),
    )


def _health(queues: list[QueueSnapshot]) -> Health:
    if not queues:
        return "unavailable"
    if all(q.availability == "unavailable" for q in queues):
        return "unavailable"
    if any(q.availability == "unavailable" for q in queues):
        return "degraded"
    if any(q.count and q.count > 0 for q in queues):
        return "degraded"
    return "healthy"


def _next_queue(queues: list[QueueSnapshot]) -> Optional[QueueCode]:
    by_code = {q.code: q for q in queues}
    for code in QUEUE_PRIORITY:
        q = by_code.get(code)
        if q is None:
            continue
        if q.availability != "available":
            continue
        if q.count is not None and q.count > 0:
            return code
    return None


def build_platform_ops_overview(conn: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    """Compose authoritative queue overview. Never fabricates zero for missing sources."""
    queues = [
        _build_queue("artist_requests", _count_artist_requests(conn)),
        _build_queue("catalog_reviews", _count_catalog_reviews(conn)),
        _build_queue("audio_unresolved", _count_audio_unresolved(conn)),
        _build_queue("incidents", _count_incidents(conn)),
    ]
    next_q = _next_queue(queues)
    has_pending = any(
        q.availability == "available" and q.count is not None and q.count > 0 for q in queues
    )
    return {
        "health": _health(queues),
        "generated_at": _utc_now(),
        "queues": [
            {
                "code": q.code,
                "count": q.count,
                "availability": q.availability,
                "severity": q.severity,
            }
            for q in queues
        ],
        "next_queue": next_q,
        "has_pending_work": has_pending,
    }
