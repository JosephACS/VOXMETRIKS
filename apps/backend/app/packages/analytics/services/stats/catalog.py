"""Catalog-oriented stats queries (energy, top tracks, loads, growth)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import duckdb

from app.core.database import get_table_columns, table_exists
from app.core.query_helpers import count_rows, fetch_rows
from app.packages.catalog.services.tracks.playback_availability import playable_track_sql

logger = logging.getLogger(__name__)


def get_energia_distribution(conn: duckdb.DuckDBPyConnection) -> List[Dict[str, Any]]:
    rows, _ = fetch_rows(
        conn, "agg_distribucion_energia",
        columns=[
            "rango_energia", "cantidad_tracks",
            "popularidad_promedio", "danceability_promedio",
        ],
        order_by="rango_energia",
    )
    return rows


def get_top_tracks_by_popularity(
    conn: duckdb.DuckDBPyConnection, limit: int = 10
) -> List[Dict[str, Any]]:
    """Top tracks — prefer pre-aggregated ``agg_tracks_populares`` when populated."""
    lim = int(limit)
    playable = playable_track_sql(conn)
    if table_exists(conn, "agg_tracks_populares"):
        agg_count = conn.execute(
            "SELECT COUNT(*) FROM agg_tracks_populares WHERE popularity IS NOT NULL"
        ).fetchone()[0]
        if agg_count:
            rows = conn.execute(
                f"""
                SELECT
                    a.id_track,
                    a.nombre_track,
                    COALESCE(a.nombre_artista, '—') AS nombre_artista,
                    dt.id_artista,
                    dt.id_genero,
                    a.popularity,
                    a.energy,
                    a.danceability,
                    a.valence
                FROM agg_tracks_populares a
                JOIN dim_track dt ON dt.id_track = a.id_track
                WHERE a.popularity IS NOT NULL
                  AND ({playable})
                ORDER BY a.popularity DESC
                LIMIT ?
                """,
                [lim],
            ).fetchall()
            cols = [
                "id_track", "nombre_track", "nombre_artista", "id_artista",
                "id_genero", "popularity", "energy", "danceability", "valence",
            ]
            return [dict(zip(cols, row)) for row in rows]

    track_cols = set(get_table_columns(conn, "dim_track"))
    optional_feats = [c for c in ("energy", "danceability", "valence") if c in track_cols]
    feat_sql = "".join(f", dt.{c}" for c in optional_feats)
    rows = conn.execute(
        f"""
        SELECT
            dt.id_track,
            dt.nombre_track,
            COALESCE(da.nombre_artista, '—') AS nombre_artista,
            dt.id_artista,
            dt.id_genero,
            dt.popularity{feat_sql}
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        WHERE dt.popularity IS NOT NULL
          AND ({playable})
        ORDER BY dt.popularity DESC
        LIMIT ?
        """,
        [lim],
    ).fetchall()

    cols = [
        "id_track", "nombre_track", "nombre_artista", "id_artista",
        "id_genero", "popularity", *optional_feats,
    ]
    out: List[Dict[str, Any]] = []
    for row in rows:
        item = dict(zip(cols, row))
        for feat in ("energy", "danceability", "valence"):
            item.setdefault(feat, None)
        out.append(item)
    return out


def get_last_loads(
    conn: duckdb.DuckDBPyConnection, limit: int = 5
) -> List[Dict[str, Any]]:
    rows, _ = fetch_rows(
        conn, "ctl_carga_dataset",
        columns=["id_carga", "fecha_carga", "modo", "registros_nuevos", "total_raw", "estado"],
        order_by="id_carga DESC",
        limit=limit,
    )
    result = []
    for r in rows:
        result.append({
            "id_carga": r.get("id_carga"),
            "fecha_carga": str(r["fecha_carga"]) if r.get("fecha_carga") else None,
            "modo": r.get("modo", "—"),
            "registros_nuevos": r.get("registros_nuevos", 0),
            "total_raw": r.get("total_raw", 0),
            "estado": r.get("estado", "—"),
        })
    return result


def get_catalog_growth(
    conn: duckdb.DuckDBPyConnection,
    months: int = 12,
) -> List[Dict[str, Any]]:
    """
    Catalog growth series from ctl_carga_dataset (real warehouse loads).
    Falls back to current dim_track count if no load history exists.
    """
    months = max(3, min(int(months), 24))
    current = count_rows(conn, "dim_track")

    try:
        rows = conn.execute("""
            SELECT
                fecha_carga,
                COALESCE(total_raw, 0) AS total_raw,
                COALESCE(registros_nuevos, 0) AS registros_nuevos
            FROM ctl_carga_dataset
            ORDER BY fecha_carga ASC
        """).fetchall()
    except Exception:
        logger.exception("get_catalog_growth: ctl_carga_dataset unavailable")
        rows = []

    points: List[Dict[str, Any]] = []
    if rows:
        for r in rows:
            fecha = str(r[0]) if r[0] else ""
            label = fecha[:7] if len(fecha) >= 7 else fecha
            points.append({
                "label": label,
                "total": int(r[1] or 0),
                "added": int(r[2] or 0),
            })
        if points and points[-1]["total"] < current:
            points.append({
                "label": "actual",
                "total": current,
                "added": max(0, current - points[-1]["total"]),
            })
    else:
        points.append({"label": "actual", "total": current, "added": 0})

    if len(points) > months:
        points = points[-months:]
    while len(points) < months and len(points) >= 1:
        first = points[0]
        prev_total = max(0, first["total"] - first.get("added", 0))
        points.insert(0, {
            "label": "…",
            "total": prev_total,
            "added": 0,
        })

    values = [p["total"] for p in points]
    max_v = max(values) if values else 1
    return [
        {**p, "normalized": round((p["total"] / max_v) * 100, 1) if max_v else 0}
        for p in points
    ]
