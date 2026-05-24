"""backend/services/stats_service.py"""

from __future__ import annotations

from typing import Any, Dict, List

import duckdb

from .base_service import count_rows, fetch_rows

# Límites validados — DuckDB aguanta millones; el cuello suele ser RAM/disco en la PC.
MAX_TARGET_TOTAL = 5_000_000       # tope absoluto en dim_track
MAX_CREATE_PER_RUN = 2_000_000     # máx. filas nuevas por ejecución
WARN_CREATE_ABOVE = 500_000        # aviso UI / respuesta
SYNTHETIC_BATCH_SIZE = 100_000     # insert por lotes para no saturar memoria


def get_summary(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    """High-level counts + averages across all warehouse tables."""
    result: Dict[str, Any] = {
        "total_tracks":   count_rows(conn, "dim_track"),
        "total_artistas": count_rows(conn, "dim_artista"),
        "total_generos":  count_rows(conn, "dim_genero"),
        "total_albumes":  count_rows(conn, "dim_album"),
        "total_streams":  count_rows(conn, "fact_streaming"),
        "active_users":   count_rows(conn, "dim_usuario"),
        "total_playlists": count_rows(conn, "dim_playlist"),
    }

    try:
        row = conn.execute("""
            SELECT
                ROUND(SUM(CASE WHEN skipped THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2),
                ROUND(SUM(CASE WHEN completado THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2),
                ROUND(AVG(engagement_score), 2)
            FROM fact_streaming fs
            LEFT JOIN agg_user_activity ua ON ua.id_usuario = fs.id_usuario
        """).fetchone()
        if row:
            result["skip_rate"] = float(row[0] or 0)
            result["completion_rate"] = float(row[1] or 0)
            result["engagement_score"] = float(row[2] or 0)
    except Exception:
        pass

    # Averages from dim_track (audio features live there now)
    try:
        row = conn.execute("""
            SELECT
                AVG(popularity)    AS promedio_popularidad,
                AVG(energy)        AS promedio_energy,
                AVG(danceability)  AS promedio_danceability,
                AVG(valence)       AS promedio_valence,
                AVG(tempo)         AS promedio_tempo
            FROM dim_track
            WHERE popularity IS NOT NULL
        """).fetchone()
        if row:
            result["promedio_popularidad"]  = round(float(row[0] or 0), 1)
            result["promedio_energy"]       = round(float(row[1] or 0), 4)
            result["promedio_danceability"] = round(float(row[2] or 0), 4)
            result["promedio_valence"]      = round(float(row[3] or 0), 4)
            result["promedio_tempo"]        = round(float(row[4] or 0), 1)
    except Exception:
        result["promedio_popularidad"]  = 0.0
        result["promedio_energy"]       = 0.0
        result["promedio_danceability"] = 0.0
        result["promedio_valence"]      = 0.0
        result["promedio_tempo"]        = 0.0

    return result


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
    """
    Top tracks by popularity using dim_track (audio features are stored there)
    joined with dim_artista for the artist name.
    """
    rows = conn.execute(f"""
        SELECT
            dt.id_track,
            dt.nombre_track,
            COALESCE(da.nombre_artista, '—') AS nombre_artista,
            dt.id_artista,
            dt.id_genero,
            dt.popularity,
            dt.energy,
            dt.danceability,
            dt.valence
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        WHERE dt.popularity IS NOT NULL
        ORDER BY dt.popularity DESC
        LIMIT {int(limit)}
    """).fetchall()

    cols = [
        "id_track", "nombre_track", "nombre_artista", "id_artista",
        "id_genero", "popularity", "energy", "danceability", "valence",
    ]
    return [dict(zip(cols, row)) for row in rows]


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
            "id_carga":         r.get("id_carga"),
            "fecha_carga":      str(r["fecha_carga"]) if r.get("fecha_carga") else None,
            "modo":             r.get("modo", "—"),
            "registros_nuevos": r.get("registros_nuevos", 0),
            "total_raw":        r.get("total_raw", 0),
            "estado":           r.get("estado", "—"),
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
        # No load history — single real snapshot
        points.append({"label": "actual", "total": current, "added": 0})

    # Normalize to requested length (pad or trim)
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


def get_synthetic_limits() -> Dict[str, Any]:
    """Límites expuestos al frontend para validación antes de generar."""
    return {
        "max_target_total": MAX_TARGET_TOTAL,
        "max_create_per_run": MAX_CREATE_PER_RUN,
        "warn_create_above": WARN_CREATE_ABOVE,
        "batch_size": SYNTHETIC_BATCH_SIZE,
        "duckdb_note": (
            "DuckDB soporta millones de filas. Tiempo y disco dependen de tu PC "
            f"(~0.5–1 KB por track → 1.6M ≈ 1–2 GB en voxmetrik.duckdb)."
        ),
    }


def _insert_synthetic_batch(
    conn: duckdb.DuckDBPyConnection,
    batch_size: int,
    seq_offset: int,
    source_count: int,
    source_filter: str,
) -> None:
    max_id = conn.execute("SELECT COALESCE(MAX(id_track), 0) FROM dim_track").fetchone()[0]
    start = seq_offset + 1
    end = seq_offset + batch_size + 1

    conn.execute(f"""
        INSERT INTO dim_track (
            id_track, spotify_track_id, nombre_track,
            id_artista, id_album, id_genero, explicit, duration_ms,
            danceability, energy, loudness, speechiness, acousticness,
            instrumentalness, liveness, valence, tempo, popularity
        )
        SELECT
            {max_id} + ROW_NUMBER() OVER (ORDER BY seq.i) AS id_track,
            COALESCE(
                'syn_' || dt.spotify_track_id || '_' || seq.i,
                'syn_' || CAST(dt.id_track AS VARCHAR) || '_' || seq.i
            ) AS spotify_track_id,
            dt.nombre_track || ' [syn-' || seq.i || ']' AS nombre_track,
            dt.id_artista,
            dt.id_album,
            dt.id_genero,
            dt.explicit,
            dt.duration_ms,
            dt.danceability,
            LEAST(1.0, GREATEST(0.0, COALESCE(dt.energy, 0.5) + ((seq.i % 17) * 0.005 - 0.04))),
            dt.loudness,
            dt.speechiness,
            dt.acousticness,
            dt.instrumentalness,
            dt.liveness,
            dt.valence,
            dt.tempo,
            GREATEST(0, LEAST(100, COALESCE(dt.popularity, 0) + ((seq.i % 11) - 5)))
        FROM (
            SELECT unnest(range({start}, {end})) AS i
        ) AS seq
        INNER JOIN (
            SELECT
                dt.*,
                (ROW_NUMBER() OVER (ORDER BY dt.id_track) - 1) AS src_idx
            FROM dim_track dt
            WHERE {source_filter}
        ) dt ON (seq.i - 1) % {source_count} = dt.src_idx
    """)


def generate_synthetic_tracks(
    conn: duckdb.DuckDBPyConnection,
    *,
    target_total: int | None = None,
    multiplier: int | None = None,
) -> Dict[str, Any]:
    """
    Expand dim_track until reaching target_total rows.
    Inserts in batches (100K) for stability on consumer hardware.
    """
    if target_total is None and multiplier is None:
        raise ValueError("provide target_total or multiplier")

    before = count_rows(conn, "dim_track")
    if before == 0:
        return {
            "before": 0,
            "after": 0,
            "created": 0,
            "target_total": target_total or 0,
            "source_rows": 0,
            "batches": 0,
            "warning": None,
        }

    if target_total is None:
        if multiplier is None or multiplier < 1:
            raise ValueError("multiplier must be >= 1")
        target_total = before * multiplier

    if target_total < 1:
        raise ValueError("target_total must be >= 1")
    if target_total > MAX_TARGET_TOTAL:
        raise ValueError(
            f"target_total cannot exceed {MAX_TARGET_TOTAL:,} "
            f"(DuckDB límite del proyecto; pediste {target_total:,})"
        )

    needed = max(0, target_total - before)
    if needed == 0:
        return {
            "before": before,
            "after": before,
            "created": 0,
            "target_total": target_total,
            "source_rows": before,
            "batches": 0,
            "warning": None,
        }

    if needed > MAX_CREATE_PER_RUN:
        raise ValueError(
            f"cannot create more than {MAX_CREATE_PER_RUN:,} rows in one run "
            f"(requested {needed:,}). Usa varias ejecuciones (+100K) o baja el objetivo."
        )

    source_count = conn.execute(
        "SELECT COUNT(*) FROM dim_track WHERE nombre_track NOT LIKE '%[syn-%'"
    ).fetchone()[0]
    if source_count == 0:
        source_count = before
        source_filter = "TRUE"
    else:
        source_filter = "nombre_track NOT LIKE '%[syn-%'"

    inserted = 0
    seq_offset = 0
    batches = 0
    while inserted < needed:
        batch = min(SYNTHETIC_BATCH_SIZE, needed - inserted)
        _insert_synthetic_batch(conn, batch, seq_offset, source_count, source_filter)
        inserted += batch
        seq_offset += batch
        batches += 1

    after = count_rows(conn, "dim_track")
    created = after - before
    warning = "large" if needed >= WARN_CREATE_ABOVE else None

    try:
        id_carga = conn.execute(
            "SELECT COALESCE(MAX(id_carga), 0) + 1 FROM ctl_carga_dataset"
        ).fetchone()[0]
        conn.execute(
            """
            INSERT INTO ctl_carga_dataset
                (id_carga, fecha_carga, modo, registros_nuevos, total_raw, estado)
            VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, 'OK')
            """,
            [id_carga, f"synthetic_target_{target_total}", created, after],
        )
    except Exception:
        pass

    return {
        "before": before,
        "after": after,
        "created": created,
        "target_total": target_total,
        "source_rows": before,
        "batches": batches,
        "warning": warning,
    }