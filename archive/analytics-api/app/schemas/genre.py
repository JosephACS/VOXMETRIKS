from __future__ import annotations

from pydantic import BaseModel


class GenreTrendItem(BaseModel):
    id_genero: int
    nombre_genero: str | None = None
    streams_7d: int = 0
    streams_prev_7d: int = 0
    trend_pct: float = 0.0
    avg_popularity: float = 0.0


class GenrePopularityItem(BaseModel):
    id_genero: int
    nombre_genero: str | None = None
    popularidad_promedio: float | None = None
    energia_promedio: float | None = None
    total_tracks: int = 0
    total_artistas: int = 0


class GenreTrendsResponse(BaseModel):
    items: list[GenreTrendItem]
    total: int


class GenrePopularityResponse(BaseModel):
    items: list[GenrePopularityItem]
    total: int
