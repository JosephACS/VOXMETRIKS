"""
backend/schemas/models.py
=========================
Pydantic v2 response models + Create/Update models for CRUD.
All fields match the DuckDB warehouse schema exactly.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


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
    popularity:         Optional[int]   = None
    nombre_artista:   Optional[str] = None
    nombre_genero:    Optional[str] = None

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


class AudioSource(BaseModel):
    """Resolved playback source for a track."""
    track_id:         int
    provider:         str = "youtube"
    youtube_video_id: Optional[str] = None
    source_ref:       Optional[str] = None
    playable_url:     Optional[str] = None
    query:            Optional[str] = None
    status:           str  # ok | not_found | disabled | pending | error
    confidence_score: Optional[float] = None


class CoverArt(BaseModel):
    """Resolved real cover-art image URL for a track (iTunes)."""
    track_id:  int
    image_url: Optional[str] = None
    status:    str  # ok | not_found


class ArtistCoverArt(BaseModel):
    """Resolved artist image URL (iTunes musicArtist)."""
    artist_id: int
    image_url: Optional[str] = None
    status:    str  # ok | not_found


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


class CursorPaginatedResponse(BaseModel):
    """Keyset pagination — stable for deep pages (no OFFSET scan)."""
    limit:        int
    items:        list
    next_cursor:  Optional[str] = None
    has_more:     bool = False
    total:        Optional[int] = None
    page:         Optional[int] = None


# ── Delete response ───────────────────────────────────────────────────────────

class DeleteResponse(BaseModel):
    deleted: bool
    id:      int


# ── Streaming app (playlists / favorites) ─────────────────────────────────────

class PlaylistCreate(BaseModel):
    name:        str
    description: Optional[str] = None

class PlaylistUpdate(BaseModel):
    name:        Optional[str] = None
    description: Optional[str] = None

class PlaylistTrackAdd(BaseModel):
    track_id: int

class PlaylistSummary(BaseModel):
    id:           int
    name:         str
    description:  Optional[str] = None
    created_at:   Optional[str] = None
    total_tracks: int = 0
    cover_track_id: Optional[int] = None

class PlaylistTrackItem(BaseModel):
    id_track:       int
    nombre_track:   Optional[str] = None
    id_artista:     Optional[int] = None
    id_genero:      Optional[int] = None
    duration_ms:    Optional[int] = None
    popularity:     Optional[int] = None
    nombre_artista: Optional[str] = None
    nombre_genero:  Optional[str] = None

class PlaylistDetail(PlaylistSummary):
    tracks: List[PlaylistTrackItem] = []

class FavoriteTrack(BaseModel):
    id_track:       int
    nombre_track:   Optional[str] = None
    id_artista:     Optional[int] = None
    id_genero:      Optional[int] = None
    duration_ms:    Optional[int] = None
    popularity:     Optional[int] = None
    nombre_artista: Optional[str] = None
    nombre_genero:  Optional[str] = None
    added_at:       Optional[str] = None

class TrackSearchResult(BaseModel):
    id_track:       int
    spotify_track_id: Optional[str] = None
    nombre_track:   Optional[str] = None
    id_artista:     Optional[int] = None
    id_genero:      Optional[int] = None
    duration_ms:    Optional[int] = None
    popularity:     Optional[int] = None
    nombre_artista: Optional[str] = None
    nombre_genero:  Optional[str] = None

class TrackDetail(BaseModel):
    id_track:       int
    spotify_track_id: Optional[str] = None
    nombre_track:   Optional[str] = None
    id_artista:     Optional[int] = None
    id_album:       Optional[int] = None
    id_genero:      Optional[int] = None
    explicit:       Optional[bool] = None
    duration_ms:    Optional[int] = None
    popularity:     Optional[int] = None
    danceability:   Optional[float] = None
    energy:         Optional[float] = None
    loudness:       Optional[float] = None
    speechiness:    Optional[float] = None
    acousticness:   Optional[float] = None
    instrumentalness: Optional[float] = None
    liveness:       Optional[float] = None
    valence:        Optional[float] = None
    tempo:          Optional[float] = None
    nombre_artista: Optional[str] = None
    nombre_genero:  Optional[str] = None


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status:       str
    version:      str
    table_count:  int = 0
    database:     Optional[str] = None
    tables:       List[str] = Field(default_factory=list)


# ── Users (Package 2) ─────────────────────────────────────────────────────────

class UserPreferences(BaseModel):
    dark_mode: bool = True
    audio_quality: str = "high"
    recommendations_enabled: bool = True
    privacy_public: bool = False


class UserPublic(BaseModel):
    id: int
    username: str
    email: str
    role: str = "user"
    plan: str
    favorite_genre: Optional[str] = None
    created_at: Optional[str] = None
    preferences: UserPreferences = UserPreferences()
    email_verified: bool = True
    auth_provider: str = "local"


class UserLogin(BaseModel):
    login: str
    password: str
    remember: bool = True


class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    favorite_genre: Optional[str] = None


class VerifyEmailRequest(BaseModel):
    email: str
    code: str


class ResendCodeRequest(BaseModel):
    email: str


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    email: str
    code: str
    new_password: str


class GoogleLoginRequest(BaseModel):
    credential: str


class AuthConfig(BaseModel):
    google_client_id: str = ""
    email_verification_enabled: bool = True


class UserStats(BaseModel):
    favorites_count: int = 0
    playlists_count: int = 0


class UserProfile(UserPublic):
    stats: UserStats = UserStats()
    playlists: List[PlaylistSummary] = []


class UserPreferencesUpdate(BaseModel):
    dark_mode: Optional[bool] = None
    audio_quality: Optional[str] = None
    recommendations_enabled: Optional[bool] = None
    privacy_public: Optional[bool] = None
    favorite_genre: Optional[str] = None
