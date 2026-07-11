"""API layer — route aggregation."""

from app.api.routes import artists, audit, genres, recommendations, streams, system, users

__all__ = [
    "artists",
    "audit",
    "genres",
    "recommendations",
    "streams",
    "system",
    "users",
]
