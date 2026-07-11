from __future__ import annotations

from app.db.duckdb_client import DuckDBClient
from app.services._warehouse import table_exists
from app.services.scoring._helpers import min_max_scale


class TrendingBoost:
    """Artist growth + genre trend signals from GOLD aggregates."""

    def __init__(self, client: DuckDBClient) -> None:
        self._client = client
        self._artist_growth: dict[int, float] = {}
        self._genre_trend: dict[int, float] = {}
        self._loaded = False

    def ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._artist_growth = self._load_artist_growth()
        self._genre_trend = self._load_genre_trends()
        self._loaded = True

    def score_track(self, *, artist_id: int | None, genre_id: int | None) -> float:
        self.ensure_loaded()
        scores: list[float] = []
        if artist_id is not None and artist_id in self._artist_growth:
            scores.append(self._artist_growth[artist_id])
        if genre_id is not None and genre_id in self._genre_trend:
            scores.append(self._genre_trend[genre_id])
        if not scores:
            return 0.2
        return round(sum(scores) / len(scores), 4)

    def _load_artist_growth(self) -> dict[int, float]:
        if not table_exists(self._client, "agg_artist_growth"):
            return {}
        rows = self._client.fetch_all(
            """
            SELECT id_artista, growth_pct FROM agg_artist_growth
            WHERE growth_pct IS NOT NULL
            """,
            label="trending_artist_growth",
        )
        if not rows:
            return {}
        values = [float(r["growth_pct"] or 0) for r in rows]
        lo, hi = min(values), max(values)
        return {
            int(r["id_artista"]): min_max_scale(float(r["growth_pct"] or 0), lo, hi)
            for r in rows
        }

    def _load_genre_trends(self) -> dict[int, float]:
        if table_exists(self._client, "agg_genre_trends"):
            rows = self._client.fetch_all(
                "SELECT id_genero, trend_pct FROM agg_genre_trends WHERE trend_pct IS NOT NULL",
                label="trending_genre_trends",
            )
        elif table_exists(self._client, "agg_genero_popularidad"):
            rows = self._client.fetch_all(
                """
                SELECT id_genero, popularidad_promedio AS trend_pct
                FROM agg_genero_popularidad
                """,
                label="trending_genre_popularity",
            )
        else:
            return {}
        if not rows:
            return {}
        values = [float(r["trend_pct"] or 0) for r in rows]
        lo, hi = min(values), max(values)
        return {
            int(r["id_genero"]): min_max_scale(float(r["trend_pct"] or 0), lo, hi)
            for r in rows
        }
