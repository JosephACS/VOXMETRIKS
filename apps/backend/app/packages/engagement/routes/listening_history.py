"""Listening history API — account-scoped personal playback history."""

from __future__ import annotations

from typing import Any, List, Optional

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.database import get_conn, get_write_conn
from app.packages.engagement.services import listening_history_service as lhs
from app.packages.identity.services.auth_deps import require_user_id

router = APIRouter(prefix="/listening-history", tags=["Listening History"])


class StartRequest(BaseModel):
    track_id: int = Field(gt=0)
    event_key: Optional[str] = None
    source: Optional[str] = Field(default="player", max_length=64)
    progress_ms: Optional[int] = Field(default=None, ge=0)
    listened_ms: Optional[int] = Field(default=None, ge=0)


class ProgressRequest(BaseModel):
    event_key: str = Field(min_length=1, max_length=128)
    progress_ms: Optional[int] = Field(default=None, ge=0)
    listened_ms: Optional[int] = Field(default=None, ge=0)
    completed: Optional[bool] = None


class CompleteRequest(BaseModel):
    event_key: str = Field(min_length=1, max_length=128)
    progress_ms: Optional[int] = Field(default=None, ge=0)
    listened_ms: Optional[int] = Field(default=None, ge=0)


class MigrateEntry(BaseModel):
    id_track: int = Field(gt=0)
    viewed_at: Optional[str] = None
    nombre_track: Optional[str] = None
    nombre_artista: Optional[str] = None


class MigrateRequest(BaseModel):
    entries: List[MigrateEntry] = Field(default_factory=list)


@router.post("/start", summary="Register playback start (idempotent by event_key)")
def start(
    body: StartRequest,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return lhs.start_playback(
            conn,
            user_id,
            body.track_id,
            event_key=body.event_key,
            source=body.source,
            progress_ms=body.progress_ms,
            listened_ms=body.listened_ms,
        )
    except ValueError as exc:
        if str(exc) == "track_not_found":
            raise HTTPException(status_code=404, detail="Track not found") from exc
        raise HTTPException(status_code=400, detail="Invalid request") from exc


@router.post("/progress", summary="Update playback progress (idempotent)")
def progress(
    body: ProgressRequest,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return lhs.update_progress(
            conn,
            user_id,
            body.event_key,
            progress_ms=body.progress_ms,
            listened_ms=body.listened_ms,
            completed=body.completed,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="History entry not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid request") from exc


@router.post("/complete", summary="Mark playback completed")
def complete(
    body: CompleteRequest,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return lhs.complete_playback(
            conn,
            user_id,
            body.event_key,
            progress_ms=body.progress_ms,
            listened_ms=body.listened_ms,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="History entry not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid request") from exc


@router.get("", summary="Paginated personal listening history")
def list_items(
    page: int = Query(1, ge=1),
    limit: int = Query(30, ge=1, le=200),
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return lhs.list_history(conn, user_id, page=page, limit=limit)


@router.get("/recent", summary="Recent distinct tracks for continue listening")
def recent(
    limit: int = Query(8, ge=1, le=50),
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return {"items": lhs.list_recent(conn, user_id, limit=limit)}


@router.post("/clear", summary="Clear own listening history (requires confirm=true)")
def clear_all(
    confirm: bool = Query(False),
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "confirmation_required",
                "message": "Pass confirm=true to clear history",
            },
        )
    deleted = lhs.clear_history(conn, user_id)
    return {"cleared": True, "deleted": deleted}


@router.delete("/{entry_id}", summary="Delete own history entry")
def delete_one(
    entry_id: int,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    ok = lhs.delete_entry(conn, user_id, entry_id)
    if not ok:
        raise HTTPException(status_code=404, detail="History entry not found")
    return {"removed": True, "id": entry_id}


@router.post("/migrate", summary="Idempotent migration of localStorage history")
def migrate(
    body: MigrateRequest,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    payload = [e.model_dump() for e in body.entries]
    return lhs.migrate_local_entries(conn, user_id, payload)
