"""
Shared schemas - Pydantic models for request/response validation
"""

from .models import (
    # Dimensions
    Artista, ArtistaCreate, ArtistaUpdate,
    Genero, GeneroCreate, GeneroUpdate,
    Album,
    Track, TrackCreate, TrackUpdate,
    # Fact
    AudioFeatures,
    # Aggregations
    TopArtista,
    GeneroPopularidad,
    DistribucionEnergia,
    # Generic wrappers
    PaginatedResponse,
    DeleteResponse,
    HealthResponse,
)

__all__ = [
    # Dimensions
    "Artista", "ArtistaCreate", "ArtistaUpdate",
    "Genero", "GeneroCreate", "GeneroUpdate",
    "Album",
    "Track", "TrackCreate", "TrackUpdate",
    # Fact
    "AudioFeatures",
    # Aggregations
    "TopArtista",
    "GeneroPopularidad",
    "DistribucionEnergia",
    # Generic wrappers
    "PaginatedResponse",
    "DeleteResponse",
    "HealthResponse",
]
