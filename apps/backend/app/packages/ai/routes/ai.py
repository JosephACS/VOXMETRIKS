"""VOXMETRIKS AI API — Phase 6."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import duckdb
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.database import get_conn, get_write_conn
from app.packages.ai.service import AIService
from app.packages.streaming.services.playlist_service import create_playlist, add_track_to_playlist
from app.packages.users.services.auth_deps import get_optional_user_id, require_user_id

router = APIRouter(prefix="/ai", tags=["VOXMETRIKS AI"])


class NLSearchBody(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)


class PlaylistPreviewBody(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=500)
    limit: int = Field(20, ge=5, le=40)


class PlaylistConfirmBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str = Field("", max_length=500)
    track_ids: List[int] = Field(..., min_length=1, max_length=50)


def _svc(conn: duckdb.DuckDBPyConnection = Depends(get_conn)) -> AIService:
    return AIService(conn)


@router.get("/provider/status", summary="Active AI provider and fallback info")
def provider_status(svc: AIService = Depends(_svc)):
    return svc.provider_status()


@router.post("/search/natural", summary="Natural language search → tracks")
def natural_search(body: NLSearchBody, svc: AIService = Depends(_svc)):
    return svc.search_tracks(body.query)


@router.post("/playlist/preview", summary="Preview AI playlist (no save)")
def playlist_preview(
    body: PlaylistPreviewBody,
    user_id: int = Depends(require_user_id),
    svc: AIService = Depends(_svc),
):
    return svc.preview_playlist(user_id, body.prompt, limit=body.limit)


@router.post("/playlist/confirm", summary="Save playlist after user confirmation")
def playlist_confirm(
    body: PlaylistConfirmBody,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    result = create_playlist(conn, user_id, body.name, description=body.description or None)
    pid = result["id"]
    added = 0
    for tid in body.track_ids:
        if add_track_to_playlist(conn, pid, tid, user_id):
            added += 1
    return {"playlist_id": pid, "name": body.name, "tracks_added": added, "confirmed": True}


@router.get("/explain/recommendation/{track_id}", summary="Explain why a track was recommended")
def explain_recommendation(
    track_id: int,
    user_id: int = Depends(require_user_id),
    svc: AIService = Depends(_svc),
):
    return svc.explain_track(user_id, track_id)


@router.get("/mood-profile", summary="Extended mood / listener profile")
def mood_profile(user_id: int = Depends(require_user_id), svc: AIService = Depends(_svc)):
    return svc.mood_profile(user_id)


@router.get("/dj/session", summary="AI DJ listening blocks")
def dj_session(
    user_id: int = Depends(require_user_id),
    svc: AIService = Depends(_svc),
):
    return svc.dj_session(user_id)


@router.get("/widgets/intent", summary="Intent-based home widgets")
def intent_widgets(user_id: int = Depends(require_user_id), svc: AIService = Depends(_svc)):
    return {"widgets": svc.intent_widgets(user_id)}
