"""
Shared schemas - Pydantic models for request/response validation
"""

from .models import (
    Album,
    # Dimensions
    Artista,
    ArtistaCreate,
    ArtistaUpdate,
    # Fact
    AudioFeatures,
    DeleteResponse,
    DistribucionEnergia,
    Genero,
    GeneroCreate,
    GeneroPopularidad,
    GeneroUpdate,
    HealthResponse,
    # Generic wrappers
    PaginatedResponse,
    # Aggregations
    TopArtista,
    Track,
    TrackCreate,
    TrackUpdate,
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
