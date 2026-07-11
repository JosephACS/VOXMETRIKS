from __future__ import annotations

from dataclasses import dataclass

import duckdb
from fastapi import Depends

from app.core.db import get_db
from app.services import (
    artist_service,
    audit_service,
    genre_service,
    recommendation_service,
    stream_service,
    system_service,
    user_service,
)


@dataclass(frozen=True)
class ArtistServiceDep:
    _conn: duckdb.DuckDBPyConnection

    def get_growth(self) -> dict:
        return artist_service.get_artist_growth(self._conn)

    def get_top(self, limit: int) -> dict:
        return artist_service.get_top_artists(self._conn, limit=limit)


@dataclass(frozen=True)
class StreamServiceDep:
    _conn: duckdb.DuckDBPyConnection

    def get_daily(self, days: int) -> dict:
        return stream_service.get_daily_streams(self._conn, days=days)

    def get_engagement(self) -> dict:
        return stream_service.get_engagement_analysis(self._conn)


@dataclass(frozen=True)
class GenreServiceDep:
    _conn: duckdb.DuckDBPyConnection

    def get_trends(self, limit: int) -> dict:
        return genre_service.get_genre_trends(self._conn, limit=limit)

    def get_popularity(self, limit: int) -> dict:
        return genre_service.get_genre_popularity(self._conn, limit=limit)


@dataclass(frozen=True)
class RecommendationServiceDep:
    _conn: duckdb.DuckDBPyConnection

    def get_tracks(self, limit: int) -> dict:
        return recommendation_service.get_top_recommendations(self._conn, limit=limit)


@dataclass(frozen=True)
class UserServiceDep:
    _conn: duckdb.DuckDBPyConnection

    def get_segments(self) -> dict:
        return user_service.get_user_segments(self._conn)

    def get_retention(self) -> dict:
        return user_service.get_retention_analysis(self._conn)


@dataclass(frozen=True)
class AuditServiceDep:
    _conn: duckdb.DuckDBPyConnection

    def get_pipeline(self) -> dict:
        return audit_service.get_pipeline_health(self._conn)

    def get_data_quality(self) -> dict:
        return audit_service.get_data_quality(self._conn)


@dataclass(frozen=True)
class SystemServiceDep:
    _conn: duckdb.DuckDBPyConnection

    def get_full_health(self) -> dict:
        return system_service.get_full_health(self._conn)


def get_artist_service(conn: duckdb.DuckDBPyConnection = Depends(get_db)) -> ArtistServiceDep:
    return ArtistServiceDep(_conn=conn)


def get_stream_service(conn: duckdb.DuckDBPyConnection = Depends(get_db)) -> StreamServiceDep:
    return StreamServiceDep(_conn=conn)


def get_genre_service(conn: duckdb.DuckDBPyConnection = Depends(get_db)) -> GenreServiceDep:
    return GenreServiceDep(_conn=conn)


def get_recommendation_service(
    conn: duckdb.DuckDBPyConnection = Depends(get_db),
) -> RecommendationServiceDep:
    return RecommendationServiceDep(_conn=conn)


def get_user_service(conn: duckdb.DuckDBPyConnection = Depends(get_db)) -> UserServiceDep:
    return UserServiceDep(_conn=conn)


def get_audit_service(conn: duckdb.DuckDBPyConnection = Depends(get_db)) -> AuditServiceDep:
    return AuditServiceDep(_conn=conn)


def get_system_service(conn: duckdb.DuckDBPyConnection = Depends(get_db)) -> SystemServiceDep:
    return SystemServiceDep(_conn=conn)
