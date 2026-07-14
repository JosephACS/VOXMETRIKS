from __future__ import annotations

from app.core.logging import get_logger
from app.db.duckdb_client import DuckDBClient, get_duckdb_client
from app.models.schemas import (
    SearchArtistHit,
    SearchPlaylistHit,
    SearchResponse,
    SearchTrackHit,
)
from app.services._warehouse import table_column_names, table_exists

logger = get_logger(__name__)


class SearchService:
    """Catalog search across tracks, artists, and playlists."""

    def __init__(self, client: DuckDBClient | None = None) -> None:
        self._client = client or get_duckdb_client()

    def search(self, query: str, *, limit: int = 20) -> SearchResponse:
        q = query.strip()
        if not q:
            return SearchResponse(query=q, tracks=[], artists=[], playlists=[])

        pattern = f"%{q}%"
        per_type = max(1, min(limit, 50))

        tracks: list[SearchTrackHit] = []
        if table_exists(self._client, "dim_track"):
            rows = self._client.fetch_all(
                """
                SELECT
                    dt.id_track,
                    dt.nombre_track AS track_name,
                    da.nombre_artista AS artist
                FROM dim_track dt
                LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
                WHERE LOWER(dt.nombre_track) LIKE LOWER(?)
                   OR LOWER(COALESCE(da.nombre_artista, '')) LIKE LOWER(?)
                ORDER BY dt.popularity DESC NULLS LAST, dt.nombre_track
                LIMIT ?
                """,
                [pattern, pattern, per_type],
                label="search_tracks",
            )
            tracks = [
                SearchTrackHit(
                    id_track=int(r["id_track"]),
                    track_name=str(r["track_name"] or ""),
                    artist=r.get("artist"),
                )
                for r in rows
            ]

        artists: list[SearchArtistHit] = []
        if table_exists(self._client, "dim_artista"):
            rows = self._client.fetch_all(
                """
                SELECT id_artista, nombre_artista AS artist_name
                FROM dim_artista
                WHERE LOWER(nombre_artista) LIKE LOWER(?)
                ORDER BY nombre_artista
                LIMIT ?
                """,
                [pattern, per_type],
                label="search_artists",
            )
            artists = [
                SearchArtistHit(
                    id_artista=int(r["id_artista"]),
                    artist_name=str(r["artist_name"] or ""),
                )
                for r in rows
            ]

        playlists: list[SearchPlaylistHit] = []
        if table_exists(self._client, "app_playlist"):
            rows = self._client.fetch_all(
                """
                SELECT id AS id_playlist, name AS playlist_name
                FROM app_playlist
                WHERE LOWER(name) LIKE LOWER(?)
                ORDER BY name
                LIMIT ?
                """,
                [pattern, per_type],
                label="search_app_playlists",
            )
            playlists.extend(
                SearchPlaylistHit(
                    id_playlist=int(r["id_playlist"]),
                    playlist_name=str(r["playlist_name"] or ""),
                    source="personal",
                )
                for r in rows
            )
        if table_exists(self._client, "dim_playlist"):
            cols = table_column_names(self._client, "dim_playlist")
            name_col = "nombre" if "nombre" in cols else (
                "nombre_playlist" if "nombre_playlist" in cols else None
            )
            if name_col:
                remaining = max(1, per_type - len(playlists))
                rows = self._client.fetch_all(
                    f"""
                    SELECT id_playlist, {name_col} AS playlist_name
                    FROM dim_playlist
                    WHERE LOWER({name_col}) LIKE LOWER(?)
                    ORDER BY {name_col}
                    LIMIT ?
                    """,
                    [pattern, remaining],
                    label="search_dim_playlists",
                )
                playlists.extend(
                    SearchPlaylistHit(
                        id_playlist=int(r["id_playlist"]),
                        playlist_name=str(r["playlist_name"] or ""),
                        source="catalog",
                    )
                    for r in rows
                )

        return SearchResponse(
            query=q,
            tracks=tracks,
            artists=artists,
            playlists=playlists,
        )
