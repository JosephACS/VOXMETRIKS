from __future__ import annotations

from pydantic import BaseModel, Field


class ArtistGrowthItem(BaseModel):
    id_artista: int
    nombre_artista: str | None = None
    streams_7d: int = 0
    streams_30d: int = 0
    growth_pct: float = 0.0
    total_followers: int = 0


class ArtistTopItem(BaseModel):
    id_artista: int
    nombre_artista: str | None = None
    promedio_popularidad: float | None = None
    total_tracks: int = 0
    total_streams: int = 0


class ArtistGrowthResponse(BaseModel):
    items: list[ArtistGrowthItem]
    total: int


class ArtistTopResponse(BaseModel):
    items: list[ArtistTopItem]
    total: int
