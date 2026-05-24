"""
backend/schemas/models.py
=========================
Pydantic v2 response models + Create/Update models for CRUD.
All fields match the DuckDB warehouse schema exactly.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class _Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ── Dimensions ────────────────────────────────────────────────────────────────

class Artista(BaseModel):
    id_artista:     int
    nombre_artista: str

class ArtistaCreate(BaseModel):
    nombre_artista: str

class ArtistaUpdate(BaseModel):
    nombre_artista: str


class Genero(BaseModel):
    id_genero:     int
    nombre_genero: str

class GeneroCreate(BaseModel):
    nombre_genero: str

class GeneroUpdate(BaseModel):
    nombre_genero: str


class Album(BaseModel):
    id_album:    int
    nombre_album: str
    id_artista:  Optional[int] = None


class Track(BaseModel):
    id_track:         int
    spotify_track_id: Optional[str] = None
    nombre_track:     str
    id_artista:       Optional[int] = None
    id_album:         Optional[int] = None
    id_genero:        Optional[int] = None
    explicit:         Optional[bool] = None
    duration_ms:      Optional[int] = None

class TrackCreate(BaseModel):
    nombre_track:     str
    spotify_track_id: Optional[str] = None
    id_artista:       Optional[int] = None
    id_album:         Optional[int] = None
    id_genero:        Optional[int] = None
    explicit:         Optional[bool] = None
    duration_ms:      Optional[int] = None

class TrackUpdate(BaseModel):
    nombre_track:     Optional[str] = None
    spotify_track_id: Optional[str] = None
    id_artista:       Optional[int] = None
    id_album:         Optional[int] = None
    id_genero:        Optional[int] = None
    explicit:         Optional[bool] = None
    duration_ms:      Optional[int] = None


# ── Fact ──────────────────────────────────────────────────────────────────────

class AudioFeatures(BaseModel):
    id_fact:          int
    id_track:         Optional[int]   = None
    popularity:       Optional[int]   = None
    danceability:     Optional[float] = None
    energy:           Optional[float] = None
    loudness:         Optional[float] = None
    speechiness:      Optional[float] = None
    acousticness:     Optional[float] = None
    instrumentalness: Optional[float] = None
    liveness:         Optional[float] = None
    valence:          Optional[float] = None
    tempo:            Optional[float] = None
    key_col:          Optional[int]   = None
    mode_col:         Optional[int]   = None
    time_signature:   Optional[int]   = None


# ── Aggregations ──────────────────────────────────────────────────────────────

class TopArtista(BaseModel):
    id_artista:           int
    nombre_artista:       Optional[str]   = None
    promedio_popularidad: Optional[float] = None
    total_tracks:         Optional[int]   = None


class GeneroPopularidad(BaseModel):
    id_genero:            int
    nombre_genero:        Optional[str]   = None
    popularidad_promedio: Optional[float] = None
    energia_promedio:     Optional[float] = None
    total_tracks:         Optional[int]   = None
    total_artistas:       Optional[int]   = None


class DistribucionEnergia(BaseModel):
    rango_energia:        str
    cantidad_tracks:      Optional[int]   = None
    popularidad_promedio: Optional[float] = None
    danceability_promedio: Optional[float] = None


# ── Generic paginated response wrapper ───────────────────────────────────────

class PaginatedResponse(BaseModel):
    total:  int
    page:   int
    limit:  int
    items:  list


# ── Delete response ───────────────────────────────────────────────────────────

class DeleteResponse(BaseModel):
    deleted: bool
    id:      int


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status:   str
    database: str
    tables:   List[str]
    version:  str
